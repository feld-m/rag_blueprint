from enum import Enum
from typing import List, Optional, Type, Union

from langfuse.client import StatefulTraceClient
from langfuse.llama_index.llama_index import LlamaIndexCallbackHandler
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.callbacks import CallbackManager, trace_method
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.indices.base_retriever import BaseRetriever
from llama_index.core.llms.llm import LLM
from llama_index.core.memory import BaseMemory, ChatMemoryBuffer
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.prompts import PromptTemplate
from pydantic import Field

from augmentation.bootstrap.configuration.configuration import (
    AugmentationConfiguration,
    _AugmentationConfiguration,
)
from augmentation.components.chat_engines.langfuse.callback_manager import (
    LlamaIndexCallbackManagerFactory,
)
from augmentation.components.guardrails.base_guardrails import (
    BaseGuardrailsEngine,
)
from augmentation.components.guardrails.registry import GuardrailsRegistry
from augmentation.components.llms.registry import LLMRegistry
from augmentation.components.postprocessors.registry import (
    PostprocessorRegistry,
)
from augmentation.components.retrievers.registry import RetrieverRegistry
from augmentation.langfuse.prompt_service import LangfusePromptServiceFactory
from core.base_factory import Factory


class SourceProcess(Enum):
    """Enumeration of possible chat processing sources.

    Attributes:
        CHAT_COMPLETION: Query from interactive chat completion interface
        DEPLOYMENT_EVALUATION: Query from automated deployment testing and evaluation
    """

    CHAT_COMPLETION = 1
    DEPLOYMENT_EVALUATION = 2


class LangfuseChatEngine(CondensePlusContextChatEngine):
    """Custom chat engine implementing Retrieval-Augmented Generation (RAG).

    Coordinates retrieval, post-processing, and response generation for RAG workflow.
    Integrates with Langfuse for tracing and Chainlit for message tracking.
    """

    chainlit_tag_format: str = Field(
        description="Format of the tag used to retrieve the trace by chainlit message id in Langfuse."
    )
    input_guardrail_prompt_template: Optional[PromptTemplate] = Field(
        description="Prompt template for validating user input compliance",
        default=None,
    )
    output_guardrail_prompt_template: Optional[PromptTemplate] = Field(
        description="Prompt template for validating response output compliance",
        default=None,
    )

    def __init__(
        self,
        retriever: BaseRetriever,
        llm: LLM,
        memory: BaseMemory,
        chainlit_tag_format: str,
        guardrails_engine: BaseGuardrailsEngine,
        context_prompt: Optional[Union[str, PromptTemplate]] = None,
        context_refine_prompt: Optional[Union[str, PromptTemplate]] = None,
        condense_prompt: Optional[Union[str, PromptTemplate]] = None,
        system_prompt: Optional[str] = None,
        skip_condense: bool = False,
        node_postprocessors: Optional[List[BaseNodePostprocessor]] = None,
        callback_manager: Optional[CallbackManager] = None,
        verbose: bool = False,
    ):
        """
        Initialize LangfuseChatEngine with retriever, LLM, and optional parameters.

        Args:
            retriever: Document retriever for RAG
            llm: Language model for response generation
            memory: Memory buffer for chat history
            chainlit_tag_format: Format for Chainlit message ID in Langfuse
            guardrails_engine: Guardrail engine for input/output validation
            context_prompt: Prompt for context generation
            context_refine_prompt: Prompt for refining context
            condense_prompt: Prompt for condensing context
            system_prompt: System prompt for LLM
            input_guardrail_prompt_template: Prompt template for input validation
            output_guardrail_prompt_template: Prompt template for output validation
            skip_condense: Flag to skip context condensing
            node_postprocessors: List of postprocessors for node processing
            callback_manager: Callback manager for tracing
            verbose: Flag for verbose output
        """
        super().__init__(
            retriever=retriever,
            llm=llm,
            memory=memory,
            context_prompt=context_prompt,
            context_refine_prompt=context_refine_prompt,
            condense_prompt=condense_prompt,
            system_prompt=system_prompt,
            skip_condense=skip_condense,
            node_postprocessors=node_postprocessors,
            callback_manager=callback_manager,
            verbose=verbose,
        )
        self.guardrails_engine = guardrails_engine
        self.chainlit_tag_format = chainlit_tag_format

    @trace_method("chat")
    def stream_chat(
        self,
        message: str,
        chat_history: Optional[List[ChatMessage]] = None,
        chainlit_message_id: str = None,
        source_process: SourceProcess = SourceProcess.CHAT_COMPLETION,
    ) -> AgentChatResponse:
        """Process a query using RAG pipeline with Langfuse tracing.

        Args:
            message: Raw query string to process
            chat_history: Optional chat history for context
            chainlit_message_id: Optional ID for linking to Chainlit message in UI
            source_process: Context identifier indicating query's origin source

        Returns:
            AgentChatResponse: Generated response from RAG pipeline with dummy streaming
        """
        self._set_chainlit_message_id(
            message_id=chainlit_message_id, source_process=source_process
        )

        guarded_response = self.guardrails_engine.input_guard(
            message=message, is_stream=True
        )
        if guarded_response:
            self._save_chat_history(
                input_message=message, output_message=guarded_response.response
            )
            return guarded_response

        response = super().chat(message=message, chat_history=chat_history)

        guarded_response = self.guardrails_engine.output_guard(
            message=response.response, is_stream=True
        )
        if guarded_response:
            self._save_chat_history(
                input_message=message, output_message=guarded_response.response
            )
            return guarded_response

        response.is_dummy_stream = True
        return response

    def get_current_langfuse_trace(self) -> StatefulTraceClient:
        """Retrieve current Langfuse trace from registered callback handler.

        Searches through callback handlers to find active LlamaIndexCallbackHandler
        and extract its associated Langfuse trace for monitoring or annotation.

        Returns:
            StatefulTraceClient: Active Langfuse trace or None if not found
        """
        for handler in self.callback_manager.handlers:
            if isinstance(handler, LlamaIndexCallbackHandler):
                return handler.trace
        return None

    def set_session_id(self, session_id: str) -> None:
        """Set session ID for Langfuse tracing to group related queries.

        Updates the session identifier in all registered Langfuse callback handlers
        to enable session-level analytics and trace grouping.

        Args:
            session_id: Unique identifier for current user session
        """
        for handler in self.callback_manager.handlers:
            if isinstance(handler, LlamaIndexCallbackHandler):
                handler.session_id = session_id

    def _set_chainlit_message_id(
        self, message_id: str, source_process: SourceProcess
    ) -> None:
        """Configure Chainlit message tracking in Langfuse trace.

        Links the current Langfuse trace to a Chainlit message ID and tags
        with the processing source context for traceability in the Langfuse UI.

        Args:
            message_id: Chainlit message identifier to reference
            source_process: Source context enum categorizing the query origin
        """
        for handler in self.callback_manager.handlers:
            if isinstance(handler, LlamaIndexCallbackHandler):
                handler.set_trace_params(
                    tags=[
                        self.chainlit_tag_format.format(message_id=message_id),
                        source_process.name.lower(),
                    ]
                )

    def _save_chat_history(
        self, input_message: str, output_message: str
    ) -> None:
        """Save chat history to memory buffer.

        Args:
            input_message: User input message
            output_message: Generated response message
        """
        self._memory.put(
            ChatMessage(role=MessageRole.USER, content=input_message)
        )
        self._memory.put(
            ChatMessage(role=MessageRole.ASSISTANT, content=output_message)
        )


class LangfuseChatEngineFactory(Factory):
    """Factory for creating configured LangfuseChatEngine instances.

    Constructs and connects components needed for the RAG pipeline.
    """

    _configuration_class: Type = AugmentationConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: AugmentationConfiguration
    ) -> LangfuseChatEngine:
        """Create and configure a LangfuseChatEngine instance from configuration.

        Instantiates all RAG pipeline components based on configuration settings,
        connects them with a shared callback manager for tracing, and assembles
        them into a complete chat engine.

        Args:
            configuration: Complete augmentation configuration containing
                           settings for all components

        Returns:
            LangfuseChatEngine: Fully configured RAG chat engine with tracing
        """
        chat_engine_configuration = configuration.augmentation.chat_engine
        llm = LLMRegistry.get(chat_engine_configuration.llm.provider).create(
            chat_engine_configuration.llm
        )
        retriever = RetrieverRegistry.get(
            chat_engine_configuration.retriever.name
        ).create(configuration)
        postprocessors = [
            PostprocessorRegistry.get(postprocessor_configuration.name).create(
                postprocessor_configuration
            )
            for postprocessor_configuration in chat_engine_configuration.postprocessors
        ]
        langfuse_callback_manager = LlamaIndexCallbackManagerFactory.create(
            configuration.augmentation.langfuse
        )
        memory = ChatMemoryBuffer(
            chat_history=[], token_limit=llm.metadata.context_window - 256
        )
        (
            condense_prompt_template,
            context_prompt_template,
            context_refine_prompt_template,
            system_prompt_template,
        ) = cls._get_prompt_templates(configuration=configuration.augmentation)
        guardrails_configuration = (
            configuration.augmentation.chat_engine.guardrails
        )
        guardrails_engine = GuardrailsRegistry.get(
            guardrails_configuration.name
        ).create(configuration=configuration.augmentation)

        retriever.callback_manager = langfuse_callback_manager
        llm.callback_manager = langfuse_callback_manager
        for postprocessor in postprocessors:
            postprocessor.callback_manager = langfuse_callback_manager

        return LangfuseChatEngine(
            retriever=retriever,
            llm=llm,
            node_postprocessors=postprocessors,
            callback_manager=langfuse_callback_manager,
            memory=memory,
            context_prompt=context_prompt_template,
            system_prompt=system_prompt_template,
            context_refine_prompt=context_refine_prompt_template,
            condense_prompt=condense_prompt_template,
            chainlit_tag_format=configuration.augmentation.langfuse.chainlit_tag_format,
            guardrails_engine=guardrails_engine,
        )

    @staticmethod
    def _get_prompt_templates(
        configuration: _AugmentationConfiguration,
    ) -> tuple:
        """Retrieves the prompt template for the augmentation process.

        Args:
            configuration: Configuration object containing prompt templates settings.

        Returns:
            Tuple of prompt templates for condensing, context generation,
            context refinement, system prompts.
        """
        langfuse_prompt_service = LangfusePromptServiceFactory.create(
            configuration=configuration.langfuse
        )

        condense_prompt_template = langfuse_prompt_service.get_prompt_template(
            prompt_name=configuration.chat_engine.prompt_templates.condense_prompt_name
        )
        context_prompt_template = langfuse_prompt_service.get_prompt_template(
            prompt_name=configuration.chat_engine.prompt_templates.context_prompt_name
        )
        context_refine_prompt_template = langfuse_prompt_service.get_prompt_template(
            prompt_name=configuration.chat_engine.prompt_templates.context_refine_prompt_name
        )
        system_prompt_template = langfuse_prompt_service.get_prompt_template(
            prompt_name=configuration.chat_engine.prompt_templates.system_prompt_name
        )

        return (
            condense_prompt_template,
            context_prompt_template,
            context_refine_prompt_template,
            system_prompt_template,
        )
