from datetime import datetime
from typing import List, AsyncGenerator, Optional, Dict, Any
import aiohttp
import asyncio
from asyncio import Lock

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    HackerNewsDatasourceConfiguration,
)
from embedding.datasources.hackernews.document import HackerNewsDocument
from embedding.datasources.core.reader import BaseReader


class HackerNewsReader(BaseReader):
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, configuration: HackerNewsDatasourceConfiguration):
        super().__init__()
        self.configuration = configuration
        self.export_limit = configuration.export_limit
        self._rate_limit_lock = Lock()
        self._last_request_time = 0

    def get_all_documents(self) -> List[HackerNewsDocument]:
        raise NotImplementedError("Use get_all_documents_async for asynchronous fetching")

    async def get_all_documents_async(self) -> List[HackerNewsDocument]:
        documents = []
        async for doc in self.read(self.export_limit):
            documents.append(doc)
        return documents

    async def read(self, limit: int = None) -> AsyncGenerator[HackerNewsDocument, None]:
        limit = limit or self.configuration.export_limit
        count = 0
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(f"{self.BASE_URL}/topstories.json") as response:
                top_stories = await response.json()
                for story_id in top_stories:
                    if count >= limit:
                        break
                    async for doc in self._process_item(story_id, session):
                        if count >= limit:
                            break
                        yield doc
                        count += 1

    async def _fetch_item(self, item_id: int, session: aiohttp.ClientSession) -> dict:
        async with self._rate_limit_lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self.configuration.request_delay:
                await asyncio.sleep(self.configuration.request_delay - elapsed)
            self._last_request_time = now
            async with session.get(f"{self.BASE_URL}/item/{item_id}.json") as response:
                response.raise_for_status()
                return await response.json()

    async def _process_item(self, item_id: int, session: aiohttp.ClientSession, depth: int = 0) -> AsyncGenerator[
        HackerNewsDocument, None]:
        if depth > self.configuration.max_depth:
            return

        item = await self._fetch_item(item_id, session)
        if not item or item.get("deleted"):
            return


        doc = HackerNewsDocument(
            text=item.get("text") or item.get("url") or "",
            metadata={
                "source": "hackernews",
                "depth": depth,
                "item_id": item_id,
                "is_story": item.get("type") == "story",
                "is_comment": item.get("type") == "comment",
                "descendants": item.get("descendants", 0),
            },
            id=str(item["id"]),
            type=item.get("type", "unknown"),
            title=item.get("title"),
            author=item.get("by"),
            time=datetime.utcfromtimestamp(item["time"]),
            url=item.get("url"),
            score=item.get("score"),
            parent=item.get("parent"),
            kids=item.get("kids", [])[:self.configuration.max_comments],
        )

        yield doc

        for kid_id in doc.get_kids():
            async for kid_doc in self._process_item(kid_id, session, depth + 1):
                yield kid_doc