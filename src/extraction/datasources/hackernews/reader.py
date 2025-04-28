from typing import Dict, Any, AsyncIterator, Optional
import logging
import httpx
import asyncio


from core.base_factory import Factory
from core.logger import LoggerConfiguration


from extraction.datasources.core.reader import BaseReader
from extraction.datasources.hackernews.client import HackerNewsClientFactory

from extraction.datasources.hackernews.configuration import (
    HackerNewsDatasourceConfiguration,
)


class HackerNewsDatasourceReader(BaseReader):
    """Reader for Hacker News data source.

    This class is responsible for reading data from the Hacker News API and
    converting it into a format suitable for further processing.
    """

    def __init__(self, configuration: HackerNewsDatasourceConfiguration, client:httpx.AsyncClient, logger: logging.Logger = LoggerConfiguration.get_logger(__name__)):
        """
        Initialize the HackerNewsDatasourceReader with the given configuration.
        Args:
            configuration (HackerNewsDatasourceConfiguration): Configuration for the Hacker News data source.
            client (AsyncClient): HTTP client for making requests to the Hacker News API.
            logger (logging.Logger): Logger instance for logging messages.
        """        
        super().__init__()
        self.client = client
        self.configuration = configuration
        self.logger = logger
        self.logger.info("HackerNewsDatasourceReader initialized with configuration: %s", configuration)
        self.item_url_template = f"{configuration.base_url}/item/{{id}}.json"
        self.top_stories_url = f"{configuration.base_url}/topstories.json"
        self.request_timeout = configuration.request_timeout


    async def _fetch_json(self, url: str) -> Optional[Any]:
        """Fetches JSON data from a given URL using httpx with error handling."""
        try:
            response = await self.client.get(url, timeout=self.request_timeout)
            response.raise_for_status() # Raise exception for 4xx/5xx status codes
            return response.json()
        except httpx.TimeoutException:
            self.logger.error(f"Timeout fetching {url} after {self.request_timeout}s")
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error fetching {url}: Status {e.response.status_code}, Response: {e.response.text}")
        except httpx.RequestError as e:
            self.logger.error(f"Request error fetching {url}: {e.__class__.__name__} - {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching or parsing JSON from {url}: {e}", exc_info=True)
        return None
    

    async def _fetch_story_details(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Fetches details for a single story ID."""
        story_url = self.item_url_template.format(id=story_id)
        details = await self._fetch_json(story_url)
        
        if details and details.get("type") == "story" and not details.get("deleted"):
            return details
        elif details:
            self.logger.debug(f"Item {story_id} is not a story (type: {details.get('type')}, deleted: {details.get('deleted')}). Skipping.")
        else:
             self.logger.warning(f"Failed to fetch details for story ID {story_id}.")
        return None


    async def read_all_async(self):
        
        top_story_ids = await self._fetch_json(self.top_stories_url)
        if not top_story_ids:  
            self.logger.error("Failed to fetch top story IDs. Aborting HackerNews extraction.")
            return

        if self.configuration.stories_limit is not None:
            top_story_ids = top_story_ids[:self.configuration.stories_limit]
            self.logger.info(f"Applying limit: {self.configuration.stories_limit} stories.")

        self.logger.info(f"Fetching details for up to {len(top_story_ids)} stories...")

        tasks = [self._fetch_story_details(story_id) for story_id in top_story_ids]
        fetched_count = 0

        # Use asyncio.as_completed for potentially faster yielding if order doesn't matter,
        # or keep asyncio.gather with batching for structured progress. Gather is often simpler.
        batch_size = self.configuration.fetch_batch_size
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            for story_data in results:
                if story_data is not None:
                    yield story_data
                    fetched_count += 1

        self.logger.info(f"Finished fetching. Yielded details for {fetched_count} stories.")



class HackerNewsDatasourceReaderFactory(Factory):
    _configuration_class = HackerNewsDatasourceConfiguration

    @classmethod
    def _create_instance(cls, configuration:HackerNewsDatasourceConfiguration)->HackerNewsDatasourceReader:
        async_client = HackerNewsClientFactory.create(configuration)
        return HackerNewsDatasourceReader(configuration=configuration, client=async_client)
