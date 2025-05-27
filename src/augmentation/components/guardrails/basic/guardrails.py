from typing import Optional

from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.llms.llm import LLM
from llama_index.core.prompts import PromptTemplate

from augmentation.bootstrap.configuration.configuration import (
    _AugmentationConfiguration,
)
from augmentation.components.guardrails.base_guardrails import (
    BaseGuardrailsEngine,
)
from augmentation.components.llms.registry import LLMRegistry
from augmentation.langfuse.prompt_service import LangfusePromptServiceFactory
from core.base_factory import Factory


# TODO: Add unit tests for guardrail engine
class BasicGuardrailsEngine(BaseGuardrailsEngine):

    def __init__(
        self,
        llm: LLM,
        input_prompt_template: PromptTemplate,
        output_prompt_template: PromptTemplate,
    ):
        """
        Initialize GuardrailsEngine with LLM and prompt templates.

        Args:
            llm: Language model for response generation
            input_prompt_template: Prompt template for validating user input compliance
            output_prompt_template: Prompt template for validating response output compliance
        """
        self.llm = llm
        self.input_prompt_template = input_prompt_template
        self.output_prompt_template = output_prompt_template

    def input_guard(
        self, message: str, is_stream: bool
    ) -> Optional[AgentChatResponse]:
        """
        Validate user input message against guardrail rules.

        Args:
            message: User input message to validate
            is_stream: Flag indicating if the response is a stream

        Returns:
            Optional[AgentChatResponse]: Response indicating if the input is allowed
        """
        if not self._is_input_allowed(message):
            return AgentChatResponse(
                response="I'm unable to answer this question as it doesn't comply with our usage guidelines.",
                sources=[],
                source_nodes=[],
                is_dummy_stream=is_stream,
            )
        return None

    def output_guard(
        self, message: str, is_stream: bool
    ) -> Optional[AgentChatResponse]:
        """
        Validate generated response message against guardrail rules.

        Args:
            message: Generated response message to validate
            is_stream: Flag indicating if the response is a stream

        Returns:
            Optional[AgentChatResponse]: Response indicating if the output is allowed
        """
        if not self._is_output_allowed(message):
            return AgentChatResponse(
                response="I apologize, but I'm unable to provide a response to this question.",
                sources=[],
                source_nodes=[],
                is_dummy_stream=is_stream,
            )
        return None

    def _is_input_allowed(self, message: str) -> bool:
        """
        Check if the input message is allowed based on guardrail rules.

        Args:
            message: User input message to validate

        Returns:
            bool: True if the input is allowed, False otherwise
        """
        prompt = self.input_prompt_template.format(message)
        resp = self.llm.complete(prompt)
        text = resp.text.lower()
        return not ("yes" in text or "true" in text)

    def _is_output_allowed(self, message: str) -> bool:
        """
        Check if the output message is allowed based on guardrail rules.

        Args:
            message: Generated response message to validate

        Returns:
            bool: True if the output is allowed, False otherwise
        """
        prompt = self.output_prompt_template.format(message)
        response = self.llm.complete(prompt)
        text = response.text.lower()
        return not ("yes" in text or "true" in text)


class BasicGuardrailsEngineFactory(Factory):
    """Factory for creating a GuardrailsEngine from AugmentationConfiguration."""

    _configuration_class = _AugmentationConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: _AugmentationConfiguration
    ) -> BasicGuardrailsEngine:
        """
        Create and configure a GuardrailsEngine instance from configuration.
        Instantiates the LLM and retrieves the prompt templates for input and output
        guardrails.

        Args:
            configuration: Configuration object containing settings for LLM and prompt templates

        Returns:
            GuardrailsEngine: Fully configured guardrail engine with LLM and prompt templates
        """
        llm_configuration = configuration.chat_engine.guardrails.llm
        llm = LLMRegistry.get(llm_configuration.provider).create(
            llm_configuration
        )
        input_guardrail_prompt_template, output_guardrail_prompt_template = (
            cls._get_prompt_templates(configuration=configuration)
        )
        return BasicGuardrailsEngine(
            llm=llm,
            input_prompt_template=input_guardrail_prompt_template,
            output_prompt_template=output_guardrail_prompt_template,
        )

    @staticmethod
    def _get_prompt_templates(
        configuration: _AugmentationConfiguration,
    ) -> tuple:
        """Retrieves the prompt template for the guardrail process.

        Args:
            configuration: Configuration object containing langfuse and prompt templates settings.

        Returns:
            Tuple of prompt templates for condensing, context generation,
            context refinement, system prompts, and guardrail prompts.
        """
        langfuse_prompt_service = LangfusePromptServiceFactory.create(
            configuration=configuration.langfuse
        )

        guardrails_configuration = configuration.chat_engine.guardrails
        input_guardrail_prompt_template = (
            langfuse_prompt_service.get_prompt_template(
                prompt_name=guardrails_configuration.input_prompt_name
            )
        )
        output_guardrail_prompt_template = (
            langfuse_prompt_service.get_prompt_template(
                prompt_name=guardrails_configuration.output_prompt_name
            )
        )

        return (
            input_guardrail_prompt_template,
            output_guardrail_prompt_template,
        )
