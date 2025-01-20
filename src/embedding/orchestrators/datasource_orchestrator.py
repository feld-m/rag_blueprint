from typing import Dict, List

from llama_index.core.schema import Document, TextNode

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    DatasourceName,
)
from embedding.datasources.core.manager import BaseDatasourceManager
from embedding.embedders.base import BaseEmbedder
from embedding.orchestrators.base import BaseDatasourceOrchestrator


class DatasourceOrchestrator(BaseDatasourceOrchestrator):
    """Orchestrator for multi-datasource content processing.

    Manages extraction, embedding and storage of content from multiple
    datasources through a unified interface.

    Attributes:
        embedder: Component for generating embeddings
        datasources: Mapping of datasource type to manager
        documents: Raw documents from datasources
        cleaned_documents: Processed documents
        nodes: Text nodes for embedding
    """

    def __init__(
        self,
        datasource_managers: Dict[DatasourceName, BaseDatasourceManager],
        embedder: BaseEmbedder,
    ):
        """Initialize orchestrator with managers and embedder.

        Args:
            datasource_managers: Mapping of datasource types to managers
            embedder: Component for generating embeddings
        """
        self.embedder = embedder
        self.datasources = datasource_managers
        self.documents: List[Document] = []
        self.cleaned_documents: List[Document] = []
        self.nodes: List[TextNode] = []

    async def extract(self):
        """Extract and process content from all datasources.

        Processes each configured datasource to extract documents,
        clean content and generate text nodes.
        """
        for datasource_manager in self.datasources.values():
            await self._extract(datasource_manager)

    def embed(self):
        """Generate embeddings for extracted content.

        Creates vector embeddings for all text nodes using
        configured embedding model.
        """
        self.embedder.embed(self.nodes)

    def save_to_vector_storage(self):
        """Persist embedded content to vector store.

        Saves all embedded text nodes to configured vector
        storage backend.
        """
        self.embedder.save(self.nodes)

    def update_vector_storage(self):
        """Update existing vector store content.

        Raises:
            NotImplementedError: Method must be implemented by subclass
        """
        raise NotImplementedError

    async def _extract(self, datasource_manager: BaseDatasourceManager) -> None:
        """Extract and store content from single datasource.

        Args:
            datasource_manager: Manager for specific datasource type

        Note:
            Updates documents, cleaned_documents and nodes lists in-place
        """
        documents, cleaned_documents, nodes = await datasource_manager.extract()
        self.documents.extend(documents)
        self.cleaned_documents.extend(cleaned_documents)
        self.nodes.extend(nodes)
