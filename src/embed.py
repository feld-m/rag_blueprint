"""
This script is used to process datasources documents and embed them into a vector storage.
In summary, this script reads, cleans, splits, and embeds datasources documents into a vector storage.
To run the script execute the following command from the root directory of the project:

> python src/embed.py
"""

import asyncio
import logging

from injector import Injector

from common.bootstrap.initializer import EmbeddingInitializer
from common.exceptions import CollectionExistsException
from embedding.orchestrators.datasource_orchestrator import (
    DatasourceOrchestrator,
)
from embedding.validators.vector_store_validators import VectorStoreValidator


async def run_embedding(injector: Injector):
    """Process and embed documents from datasources.

    Args:
        injector: Dependency injection container

    Note:
        Executes extraction, embedding and storage operations
        Exits with code 0 on success
    """
    datasource_orchestrator = injector.get(DatasourceOrchestrator)

    logging.info("Starting embedding...")

    await datasource_orchestrator.extract()
    datasource_orchestrator.embed()
    datasource_orchestrator.save_to_vector_storage()

    logging.info("Embedding finished...")
    exit(0)


def main(injector: Injector):
    """Execute embedding workflow with validation.

    Args:
        injector: Dependency injection container

    Note:
        Exits with code 100 if collection already exists
    """
    try:
        vector_store_validator = injector.get(VectorStoreValidator)
        vector_store_validator.validate()
    except CollectionExistsException as e:
        logging.info(f"{e.message}. Skipping embedding.")
        exit(100)

    asyncio.run(run_embedding(injector))


if __name__ == "__main__":
    injector = EmbeddingInitializer().init_injector()
    main(injector)
