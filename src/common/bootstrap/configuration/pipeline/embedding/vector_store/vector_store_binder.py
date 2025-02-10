from chromadb.api import ClientAPI as ChromaClient
from injector import singleton
from llama_index.core.vector_stores.types import VectorStore
from qdrant_client import QdrantClient

from common.bootstrap.base_binder import BaseBinder
from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    ChromaConfiguration,
    QDrantConfiguration,
    VectorStoreName,
)
from common.builders.client_builders import (
    ChromaClientBuilder,
    QdrantClientBuilder,
)
from common.builders.vector_store_builders import (
    ChromaStoreBuilder,
    QdrantStoreBuilder,
)
from embedding.validators.builders import (
    ChromaVectorStoreValidatorBuilder,
    QdrantVectorStoreValidatorBuilder,
)
from embedding.validators.vector_store_validators import VectorStoreValidator


class QdrantBinder(BaseBinder):
    """Binder for the Qdrant components."""

    def bind(self) -> None:
        """Bind the Qdrant components."""
        self._bind_configuration()
        self._bind_client()
        self._bind_vector_store()
        self._bind_validator()

    def _bind_configuration(self) -> None:
        """Bind the Qdrant configuration."""
        self.binder.bind(
            QDrantConfiguration,
            to=self.configuration.pipeline.embedding.vector_store,
            scope=singleton,
        )

    def _bind_client(self) -> None:
        """Bind the Qdrant client."""
        self.binder.bind(
            QdrantClient,
            to=QdrantClientBuilder.build,
            scope=singleton,
        )

    def _bind_vector_store(self) -> None:
        """Bind the Qdrant store."""
        self.binder.bind(
            VectorStore,
            to=QdrantStoreBuilder.build,
            scope=singleton,
        )

    def _bind_validator(self) -> None:
        """Bind the Qdrant vector store validator."""
        self.binder.bind(
            VectorStoreValidator,
            to=QdrantVectorStoreValidatorBuilder.build,
        )


class ChromaBinder(BaseBinder):
    """Binder for the Chroma components."""

    def bind(self) -> None:
        """Bind the Chroma components."""
        self._bind_configuration()
        self._bind_client()
        self._bind_vector_store()
        self._bind_validator()

    def _bind_configuration(self) -> None:
        """Bind the Chroma configuration."""
        self.binder.bind(
            ChromaConfiguration,
            to=self.configuration.pipeline.embedding.vector_store,
            scope=singleton,
        )

    def _bind_client(self) -> None:
        """Bind the Chroma client."""
        self.binder.bind(
            ChromaClient,
            to=ChromaClientBuilder.build,
            scope=singleton,
        )

    def _bind_vector_store(self) -> None:
        """Bind the Qdrant store."""
        self.binder.bind(
            VectorStore,
            to=ChromaStoreBuilder.build,
            scope=singleton,
        )

    def _bind_validator(self) -> None:
        """Bind the Chroma vector store validator."""
        self.binder.bind(
            VectorStoreValidator,
            to=ChromaVectorStoreValidatorBuilder.build,
        )


class VectorStoreBinder(BaseBinder):
    """Binder for the vector store component."""

    mapping = {
        VectorStoreName.QDRANT: QdrantBinder,
        VectorStoreName.CHROMA: ChromaBinder,
    }

    def bind(self) -> None:
        """Bind specific vector store based on the configuration."""
        vector_store_configuration = (
            self.configuration.pipeline.embedding.vector_store
        )
        VectorStoreBinder.mapping[vector_store_configuration.name](
            configuration=self.configuration, binder=self.binder
        ).bind()
