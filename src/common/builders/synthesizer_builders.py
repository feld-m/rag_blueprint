from injector import inject
from llama_index.core import get_response_synthesizer
from llama_index.core.prompts.base import PromptTemplate
from llama_index.core.prompts.prompt_type import PromptType
from llama_index.core.response_synthesizers import BaseSynthesizer

from common.bootstrap.configuration.pipeline.augmentation.query_engine.synthesizer.synthesizer_binding_keys import (
    BoundLLM,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.synthesizer.synthesizer_configuration import (
    TreeSynthesizerConfiguration,
)

CUSTOM_PROMPT_TEMPLATE = PromptTemplate(
    (
        "Context information from multiple sources is below.\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Rules:\n"
        "1. If given context doesn't match with the query, highlight that you don't answer based on the knowledge base.\n"
        "2. Use all relevant chunks from the context to answer the query.\n"
        "3. Provide exhaustive, long answer unless stated otherwise in the query.\n"
        "4. Using markdown format pay attention to the visual readibility of the answer.\n\n"
        "Following given rules and the context exhaustitaly answer the query.\n"
        "Query: {query_str}\n"
        "Answer: "
    ),
    prompt_type=PromptType.SUMMARY,
)


class TreeSynthesizerBuilder:
    """Builder for creating tree-based response synthesizer instances.

    Provides factory method to create configured synthesizers that use
    hierarchical summarization for response generation.
    """

    @staticmethod
    @inject
    def build(
        llm: BoundLLM,
        configuration: TreeSynthesizerConfiguration,
    ) -> BaseSynthesizer:
        """Creates a configured tree-based response synthesizer.

        Args:
            llm: Language model for response generation.
            configuration: Synthesizer settings including response mode
                and streaming options.

        Returns:
            BaseSynthesizer: Configured synthesizer instance using tree
                summarization strategy.
        """

        return get_response_synthesizer(
            llm=llm,
            response_mode=configuration.response_mode,
            streaming=configuration.streaming,
            summary_template=CUSTOM_PROMPT_TEMPLATE,
        )
