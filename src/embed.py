"""
This script is the entry point for the embedding process.
It initializes the embedding orchestrator and starts the embedding workflow.
To run the script, execute the following command from the root directory of the project:

> python src/embed.py

Optional flags:
  --clear-collection: Clear/delete the vector store collection before embedding
  --on-prem-config: Use on-premise configuration files
  --env: Specify the environment (local, test, dev, prod)
"""

import argparse
import asyncio
import logging

from core.logger import LoggerConfiguration
from embedding.bootstrap.initializer import EmbeddingInitializer
from embedding.orchestrators.registry import EmbeddingOrchestratorRegistry
from embedding.vector_stores.core.exceptions import CollectionExistsException
from embedding.vector_stores.registry import (
    VectorStoreRegistry,
    VectorStoreValidatorRegistry,
)


async def run(
    clear_collection: bool = False,
    logger: logging.Logger = LoggerConfiguration.get_logger(__name__),
):
    """
    Execute the embedding process.

    Args:
        clear_collection: If True, clear the collection before embedding
        logger: Logger instance for logging messages
    """
    initializer = EmbeddingInitializer()
    configuration = initializer.get_configuration()

    vector_store_config = configuration.embedding.vector_store

    # Clear collection if requested
    if clear_collection:
        logger.info(
            f"Clearing collection '{vector_store_config.collection_name}'..."
        )
        vector_store = VectorStoreRegistry.get(vector_store_config.name).create(
            vector_store_config
        )
        vector_store.clear()
        logger.info(
            f"Collection '{vector_store_config.collection_name}' cleared successfully."
        )
    else:
        # Only validate if we didn't just clear (to avoid false positives)
        validator = VectorStoreValidatorRegistry.get(
            vector_store_config.name
        ).create(vector_store_config)
        try:
            validator.validate()
        except CollectionExistsException as e:
            logger.info(
                f"Collection '{e.collection_name}' already exists. "
                "Skipping embedding process. Use --clear-collection to override."
            )
            return

    logger.info("Starting embedding process.")
    orchestrator = EmbeddingOrchestratorRegistry.get(
        configuration.embedding.orchestrator_name
    ).create(configuration)

    await orchestrator.embed()
    logger.info("Embedding process finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Embed documents into vector store",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--clear-collection",
        action="store_true",
        help="Clear/delete the vector store collection before embedding",
    )

    args, _ = parser.parse_known_args()
    asyncio.run(run(clear_collection=args.clear_collection))
