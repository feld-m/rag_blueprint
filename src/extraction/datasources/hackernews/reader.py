import aiohttp
from typing import AsyncIterator, Dict
from extraction.datasources.core.reader import BaseReader
from core import Factory
from extraction.datasources.hackernews.client import HackerNewsClientFactory
from extraction.datasources.hackernews.configuration import HackerNewsDatasourceConfiguration

class HackerNewsDatasourceReader(BaseReader):
    def __init__(self, configuration: HackerNewsDatasourceConfiguration, client: Dict[str, str]):
        self.configuration = configuration
        self.client = client

    async def read_all_async(self) -> AsyncIterator[dict]:
        """
        Asynchronously fetch and yield HackerNews top stories with only id, title, and URL.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(self.client["base_url"] + self.configuration.stories_endpoint) as response:
                story_ids = await response.json()
                for story_id in story_ids[:self.configuration.max_stories]:
                    async with session.get(f"{self.client['base_url']}/item/{story_id}.json") as story_response:
                        story = await story_response.json()
                        yield {
                            "id": story.get("id"),
                            "title": story.get("title"),
                            "url": story.get("url"),
                        }

class HackerNewsDatasourceReaderFactory(Factory):
    _configuration_class = HackerNewsDatasourceConfiguration

    @classmethod
    def _create_instance(cls, configuration: HackerNewsDatasourceConfiguration) -> HackerNewsDatasourceReader:
        client = HackerNewsClientFactory.create(configuration)
        return HackerNewsDatasourceReader(
            configuration=configuration,
            client=client,
        )
