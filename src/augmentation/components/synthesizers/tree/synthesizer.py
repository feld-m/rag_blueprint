from typing import Type

from llama_index.core import get_response_synthesizer
from llama_index.core.prompts.base import PromptTemplate
from llama_index.core.prompts.prompt_type import PromptType
from llama_index.postprocessor.colbert_rerank import ColbertRerank

from augmentation.components.llms.registry import LLMRegistry
from augmentation.components.synthesizers.tree.configuration import (
    TreeSynthesizerConfiguration,
)
from core import Factory

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


class TreeSynthesizerFactory(Factory):
    """Factory class for creating tree-based response synthesizers.

    This factory creates response synthesizers that process and combine
    information from multiple sources into coherent, tree-structured responses.

    Attributes:
        _configuration_class: The configuration class for the tree synthesizer.
    """

    _configuration_class: Type = TreeSynthesizerConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: TreeSynthesizerConfiguration
    ) -> ColbertRerank:
        """Creates a response synthesizer instance based on the provided configuration.

        This method initializes a language model from the registry using the
        configuration's LLM settings, then creates a response synthesizer with
        the specified parameters and custom prompt template.

        Args:
            configuration: Configuration object containing response synthesizer settings
                          including LLM provider, response mode, and streaming options.

        Returns:
            A configured response synthesizer instance.
        """
        llm = LLMRegistry.get(configuration.llm.provider).create(
            configuration.llm
        )
        return get_response_synthesizer(
            llm=llm,
            response_mode=configuration.response_mode,
            streaming=configuration.streaming,
            summary_template=CUSTOM_PROMPT_TEMPLATE,
        )
