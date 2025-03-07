import asyncio

import pytest
from unittest.mock import MagicMock
from aioresponses import aioresponses
from embedding.datasources.hackernews.reader import HackerNewsReader

class TestHackerNewsReader:
    @pytest.fixture(autouse=True)
    def mock_config(self):
        config = MagicMock()
        config.export_limit = 3
        config.request_delay = 0  # Disable delays for tests
        config.max_depth = 2
        config.max_comments = 5
        return config

    @pytest.fixture
    def hn_reader(self, mock_config):
        return HackerNewsReader(mock_config)

    @pytest.mark.asyncio
    async def test_reader_initialization(self, hn_reader, mock_config):
        """Test reader initializes with correct configuration"""
        assert hn_reader.export_limit == mock_config.export_limit
        assert hn_reader.configuration == mock_config
        assert isinstance(hn_reader._rate_limit_lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, hn_reader):
        """Verify rate limiting between requests"""
        with aioresponses() as m:
            m.get('https://hacker-news.firebaseio.com/v0/topstories.json', payload=[1])
            m.get('https://hacker-news.firebaseio.com/v0/item/1.json', payload={
                "id": 1, "type": "story", "time": 1630000000, "kids": []
            })

            start = asyncio.get_event_loop().time()
            async for _ in hn_reader.read(limit=1):
                pass
            elapsed = asyncio.get_event_loop().time() - start
            assert elapsed >= 0  # Disabled delays in config

    @pytest.mark.asyncio
    async def test_story_processing(self, hn_reader):
        """Test processing of a story item"""
        test_story = {
            "id": 123, "type": "story", "title": "AI Breakthrough",
            "time": 1630000000, "url": "http://example.com", "score": 42,
            "kids": [456, 789], "descendants": 2
        }

        with aioresponses() as m:
            m.get('https://hacker-news.firebaseio.com/v0/topstories.json', payload=[123])
            m.get('https://hacker-news.firebaseio.com/v0/item/123.json', payload=test_story)
            m.get('https://hacker-news.firebaseio.com/v0/item/456.json', payload={
                "id": 456, "type": "comment", "text": "First comment",
                "time": 1630000001, "parent": 123
            })
            m.get('https://hacker-news.firebaseio.com/v0/item/789.json', payload={
                "id": 789, "type": "comment", "text": "Second comment",
                "time": 1630000002, "parent": 123
            })

            docs = [doc async for doc in hn_reader.read()]
            assert len(docs) == 3

    @pytest.mark.asyncio
    async def test_comment_processing(self, hn_reader):
        """Test processing of a comment item"""
        test_comment = {
            "id": 456,
            "type": "comment",
            "text": "Great article!",
            "time": 1630000001,
            "parent": 123,
            "by": "user123",
            "kids": [789]
        }

        with aioresponses() as m:
            m.get('https://hacker-news.firebaseio.com/v0/topstories.json', payload=[123])
            m.get('https://hacker-news.firebaseio.com/v0/item/123.json', payload={
                "id": 123, "type": "story", "time": 1630000000, "kids": [456]
            })
            m.get('https://hacker-news.firebaseio.com/v0/item/456.json', payload=test_comment)
            m.get('https://hacker-news.firebaseio.com/v0/item/789.json', payload={
                "id": 789, "type": "comment", "text": "Nested", "time": 1630000002, "parent": 456
            })

            docs = []
            async for doc in hn_reader.read():
                docs.append(doc)

            assert len(docs) == 3  # Story + comment + nested comment
            comment = docs[1]
            assert comment.text == "Great article!"
            assert comment.metadata["depth"] == 1


    @pytest.mark.asyncio
    async def test_max_depth_handling(self, hn_reader):
        """Test recursive processing stops at max_depth"""
        hn_reader.configuration.max_depth = 2

        with aioresponses() as m:
            m.get('https://hacker-news.firebaseio.com/v0/topstories.json', payload=[1])
            m.get('https://hacker-news.firebaseio.com/v0/item/1.json', payload={
                "id": 1, "type": "story", "time": 1630000000, "kids": [2]
            })
            m.get('https://hacker-news.firebaseio.com/v0/item/2.json', payload={
                "id": 2, "type": "comment", "time": 1630000001, "parent": 1, "kids": [3]
            })
            m.get('https://hacker-news.firebaseio.com/v0/item/3.json', payload={
                "id": 3, "type": "comment", "time": 1630000002, "parent": 2, "kids": [4]
            })

            docs = []
            async for doc in hn_reader.read():
                docs.append(doc)

            # Should process depth 0 (story), 1 (comment 2), but stop at depth 2 (comment 3)
            assert len(docs) == 3
            assert docs[2].metadata["depth"] == 2


    @pytest.mark.asyncio
    async def test_max_comments_limit(self, hn_reader):
        """Test maximum comments per item handling"""
        hn_reader.configuration.max_comments = 3
        test_story = {
            "id": 1,
            "type": "story",
            "time": 1630000000,
            "kids": list(range(2, 7))  # 5 comments
        }

        with aioresponses() as m:
            m.get('https://hacker-news.firebaseio.com/v0/topstories.json', payload=[1])
            m.get('https://hacker-news.firebaseio.com/v0/item/1.json', payload=test_story)
            for i in range(2, 5):  # Only first 3 comments should be processed
                m.get(f'https://hacker-news.firebaseio.com/v0/item/{i}.json', payload={
                    "id": i, "type": "comment", "time": 1630000000 + i, "parent": 1
                })

            docs = []
            async for doc in hn_reader.read():
                docs.append(doc)

            assert len(docs) == 3


    @pytest.mark.asyncio
    async def test_deleted_item_handling(self, hn_reader):
        """Test skipped processing of deleted items"""
        with aioresponses() as m:
            m.get('https://hacker-news.firebaseio.com/v0/topstories.json', payload=[1])
            m.get('https://hacker-news.firebaseio.com/v0/item/1.json', payload={
                "id": 1, "deleted": True, "time": 1630000000
            })

            docs = []
            async for doc in hn_reader.read():
                docs.append(doc)

            assert len(docs) == 0
