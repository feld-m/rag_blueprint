from enum import Enum
from typing import List

from langfuse.client import StatefulTraceClient
from langfuse.llama_index.llama_index import LlamaIndexCallbackHandler
from llama_index.core.base.response.schema import RESPONSE_TYPE
from llama_index.core.callbacks import CallbackManager
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.response_synthesizers import BaseSynthesizer
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import QueryBundle, QueryType
from pydantic import Field


class SourceProcess(Enum):
    """Enumeration of possible query processing sources.

    Attributes:
        CHAT_COMPLETION: Query from interactive chat
        DEPLOYMENT_EVALUATION: Query from deployment testing
    """

    CHAT_COMPLETION = 1
    DEPLOYMENT_EVALUATION = 2


class RagQueryEngine(CustomQueryEngine):
    """Custom query engine implementing Retrieval-Augmented Generation (RAG).

    Coordinates retrieval, post-processing, and response generation for RAG workflow.
    Integrates with Langfuse for tracing and Chainlit for message tracking.

    Attributes:
        retriever: Component for retrieving relevant documents
        postprocessors: Chain of document post-processors
        response_synthesizer: Component for generating final responses
        callback_manager: Manager for tracing and monitoring callbacks
        chainlit_tag_format: Format string for Chainlit message IDs
    """

    retriever: BaseRetriever = Field(
        description="The retriever used to retrieve relevant nodes based on a given query."
    )
    postprocessors: List[BaseNodePostprocessor] = Field(
        description="The postprocessor used to process the retrieved nodes."
    )
    response_synthesizer: BaseSynthesizer = Field(
        description="The response synthesizer used to generate a response based on the retrieved nodes and the original query."
    )
    callback_manager: CallbackManager = Field(
        description="The callback manager used to handle callbacks."
    )
    chainlit_tag_format: str = Field(
        description="Format of the tag used to retrieve the trace by chainlit message id in Langfuse."
    )

    def query(
        self,
        str_or_query_bundle: QueryType,
        chainlit_message_id: str = None,
        source_process: SourceProcess = SourceProcess.CHAT_COMPLETION,
    ) -> RESPONSE_TYPE:
        """Process a query using RAG pipeline.

        Args:
            str_or_query_bundle: Raw query string or structured query bundle
            chainlit_message_id: Optional ID for Chainlit message tracking
            source_process: Source context of the query

        Returns:
            RESPONSE_TYPE: Generated response from RAG pipeline
        """
        self._set_chainlit_message_id(
            message_id=chainlit_message_id, source_process=source_process
        )
        return super().query(str_or_query_bundle)

    async def aquery(
        self,
        str_or_query_bundle: QueryType,
        chainlit_message_id: str = None,
        source_process: SourceProcess = SourceProcess.CHAT_COMPLETION,
    ) -> RESPONSE_TYPE:
        """Asynchronously process a query using RAG pipeline.

        Args:
            str_or_query_bundle: Raw query string or structured query bundle
            chainlit_message_id: Optional ID for Chainlit message tracking
            source_process: Source context of the query

        Returns:
            RESPONSE_TYPE: Generated response from RAG pipeline
        """
        self._set_chainlit_message_id(
            message_id=chainlit_message_id, source_process=source_process
        )
        return await super().aquery(str_or_query_bundle)

    def custom_query(self, query_str: str):
        """Execute custom RAG query processing pipeline.

        Implements retrieval, post-processing, and response synthesis stages.

        Args:
            query_str: Raw query string to process

        Returns:
            Response object containing generated answer
        """
        nodes = self.retriever.retrieve(query_str)
        for postprocessor in self.postprocessors:
            nodes = postprocessor.postprocess_nodes(
                nodes, QueryBundle(query_str)
            )
        response_obj = self.response_synthesizer.synthesize(query_str, nodes)
        return response_obj

    def get_current_langfuse_trace(self) -> StatefulTraceClient:
        """Retrieve current Langfuse trace from callback handler.

        Returns:
            StatefulTraceClient: Active Langfuse trace or None if not found
        """
        for handler in self.callback_manager.handlers:
            if isinstance(handler, LlamaIndexCallbackHandler):
                return handler.trace
        return None

    def set_session_id(self, session_id: str) -> None:
        """Set session ID for Langfuse tracing.

        Args:
            session_id: Unique identifier for current session
        """
        for handler in self.callback_manager.handlers:
            if isinstance(handler, LlamaIndexCallbackHandler):
                handler.session_id = session_id

    def _set_chainlit_message_id(
        self, message_id: str, source_process: SourceProcess
    ) -> None:
        """Configure Chainlit message tracking in Langfuse trace.

        Links Langfuse trace to Chainlit message and tags processing context.

        Args:
            message_id: Chainlit message identifier
            source_process: Source context of the query
        """
        for handler in self.callback_manager.handlers:
            if isinstance(handler, LlamaIndexCallbackHandler):
                handler.set_trace_params(
                    tags=[
                        self.chainlit_tag_format.format(message_id=message_id),
                        source_process.name.lower(),
                    ]
                )
