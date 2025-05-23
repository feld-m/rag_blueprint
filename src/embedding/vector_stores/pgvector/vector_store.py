from typing import Type

from llama_index.vector_stores.postgres import PGVectorStore

from core.base_factory import SingletonFactory
from embedding.vector_stores.pgvector.configuration import (
    PGVectorStoreConfiguration,
)


class PGVectorStoreFactory(SingletonFactory):
    """Factory for creating configured PostgreSQL vector store clients.

    This factory creates and manages a singleton instance of PGVectorStore
    for vector similarity search using the pgvector extension.
    """

    _configuration_class: Type = PGVectorStoreConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: PGVectorStoreConfiguration
    ) -> PGVectorStore:
        """Creates a PostgreSQL vector store client based on provided configuration.

        Args:
            configuration: PostgreSQL vector store connection configuration.

        Returns:
            PGVectorStore: Configured PostgreSQL vector store instance.
        """
        return PGVectorStore.from_params(
            database=configuration.database_name,
            host=configuration.host,
            password=configuration.secrets.password.get_secret_value(),
            port=configuration.port,
            user=configuration.secrets.username.get_secret_value(),
            table_name=configuration.collection_name,
            embed_dim=configuration.embed_dim,
        )
