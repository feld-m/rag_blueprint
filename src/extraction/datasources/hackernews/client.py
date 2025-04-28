from typing import Type
from httpx import AsyncClient
from core.base_factory import SingletonFactory
from extraction.datasources.hackernews.configuration import (
    HackerNewsDatasourceConfiguration,
)
from core.logger import LoggerConfiguration

class HackerNewsClientFactory(SingletonFactory):
    _configuration_class: Type = HackerNewsDatasourceConfiguration
    _async_client: AsyncClient = None
    logger = LoggerConfiguration.get_logger(__name__)

    @classmethod
    def _create_instance(cls, configuration: HackerNewsDatasourceConfiguration)-> AsyncClient:
        
        if cls._async_client is None or cls._async_client.is_closed:
            cls.logger.info("Creating new httpx async client for HackerNews.")
            # If the client is closed, create a new instance
            # Otherwise, return the existing instance
            # with the base URL from the configuration            
            cls._async_client = AsyncClient(follow_redirects=True, base_url=configuration.base_url)            
        else:
            # If the client is not closed, return the existing instance
            cls.logger.info("Returning existing httpx async client for HackerNews.")            
        return cls._async_client



    @classmethod
    async def close_client(cls) -> None:
        """
        Close the AsyncClient instance if it is not already closed.
        """
        if cls._async_client and not cls._async_client.is_closed:
            await cls._async_client.aclose()
            cls._async_client = None
            cls.logger.info("Closed httpx async client for HackerNews.")
        else:
            cls.logger.info("httpx async client for HackerNews is already closed or not initialized.")
        # Close the client if it is not already closed
        # This method should be called when the application is shutting down