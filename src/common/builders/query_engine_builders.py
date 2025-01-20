from injector import inject
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.callbacks import CallbackManager
from llama_index.core.response_synthesizers import BaseSynthesizer

from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseConfiguration,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.postprocessors.postprocessors_binding_key import (
    BoundPostprocessors,
)
from common.query_engine import RagQueryEngine


class QueryEngineBuilder:
    """Builder for creating RAG query engine instances.

    Provides factory method to create configured RagQueryEngine with retriever,
    postprocessors, synthesizer and callback management.
    """

    @staticmethod
    @inject
    def build(
        retriever: BaseRetriever,
        postprocessors: BoundPostprocessors,
        synthesizer: BaseSynthesizer,
        callback_manager: CallbackManager,
        configuration: LangfuseConfiguration,
    ) -> RagQueryEngine:
        """Creates a configured RAG query engine instance.

        Sets up callback management for components and assembles the engine.

        Args:
            retriever: Document retrieval component
            postprocessors: List of document processing steps
            synthesizer: Response generation component
            callback_manager: Callback handling for components
            configuration: Langfuse integration settings

        Returns:
            RagQueryEngine: Configured query engine instance
        """
        retriever.callback_manager = callback_manager
        synthesizer.callback_manager = callback_manager
        for postprocessor in postprocessors:
            postprocessor.callback_manager = callback_manager

        return RagQueryEngine(
            retriever=retriever,
            postprocessors=postprocessors,
            response_synthesizer=synthesizer,
            callback_manager=callback_manager,
            chainlit_tag_format=configuration.chainlit_tag_format,
        )
