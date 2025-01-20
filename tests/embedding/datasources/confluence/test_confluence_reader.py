import sys
from uuid import uuid4

sys.path.append("./src")

from typing import List
from unittest.mock import Mock

import pytest
from atlassian import Confluence
from markdownify import markdownify as md

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    ConfluenceDatasourceConfiguration,
)
from embedding.datasources.confluence.reader import ConfluenceReader


class Fixtures:

    def __init__(self):
        self.export_limit: int = None
        self.base_url: str = None
        self.spaces: List[str] = None
        self.spaces_pages: dict = {}

    def with_export_limit(self, export_limit: int) -> "Fixtures":
        self.export_limit = export_limit
        return self

    def with_base_url(self) -> "Fixtures":
        self.base_url = "https://confluence.com"
        return self

    def with_spaces(self) -> "Fixtures":
        self.spaces = ["space1", "space2"]
        return self

    def with_spaces_pages(self, number_of_pages_per_space) -> "Fixtures":
        for space in self.spaces:
            self.spaces_pages[space] = [
                self._create_page(space=space)
                for _ in range(number_of_pages_per_space)
            ]
        return self

    def _create_page(self, space: str) -> dict:
        return {
            "id": str(uuid4()),
            "body": {
                "view": {
                    "value": """
                    <div class="pretty">
                        <h1 extra="tag">Title</h1>
                        <p class="cool">Content</p>
                    </div>
                    """
                }
            },
            "history": {
                "createdDate": "2021-01-01T00:00:00",
                "lastUpdated": {"when": "2021-01-01T00:00:00"},
            },
            "_expandable": {"space": f"/space/{space}"},
            "title": f"{space} page",
            "_links": {
                "webui": f"/space/{space}/page",
            },
        }


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.configuration: ConfluenceDatasourceConfiguration = Mock(
            spec=ConfluenceDatasourceConfiguration
        )
        self.configuration.export_limit = self.fixtures.export_limit
        self.confluence_client: Confluence = Mock(spec=Confluence)
        self.service = ConfluenceReader(
            configuration=self.configuration,
            confluence_client=self.confluence_client,
        )

    def on_confluence_client_url(self) -> "Arrangements":
        self.confluence_client.url = self.fixtures.base_url
        return self

    def on_confluence_client_get_all_spaces(self) -> "Arrangements":
        self.confluence_client.get_all_spaces.return_value = {
            "results": [
                {"key": space_name} for space_name in self.fixtures.spaces
            ]
        }
        return self

    def on_confluence_client_get_all_pages_from_space(self) -> "Arrangements":
        fixtures = self.fixtures

        def mock_get_all_pages_from_space(*args, **kwargs) -> dict:
            space_pages = fixtures.spaces_pages[kwargs["space"]]
            start = kwargs["start"]
            return space_pages[start:]

        self.confluence_client.get_all_pages_from_space = Mock(
            side_effect=mock_get_all_pages_from_space
        )
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements) -> None:
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.service = arrangements.service

    def assert_documents(self, documents: List[dict]) -> None:
        all_available_pages = [
            page
            for pages in self.fixtures.spaces_pages.values()
            for page in pages
        ]

        if self.fixtures.export_limit is not None:
            assert len(documents) <= self.fixtures.export_limit
        else:
            assert len(documents) == len(all_available_pages)

        for i, actual_document in enumerate(documents):
            expected_page = all_available_pages[i]
            assert actual_document.extra_info["page_id"] == expected_page["id"]
            assert actual_document.text == md(
                expected_page["body"]["view"]["value"]
            )


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> ConfluenceReader:
        return self.arrangements.service


class TestConfluenceReader:

    @pytest.mark.parametrize(
        "export_limit,number_of_pages_per_space",
        [
            (10, 8),
            (10, 10),
            (10, 16),
            (20, 8),
            (20, 20),
            (20, 38),
            (None, 8),
            (None, 16),
        ],
    )
    @pytest.mark.asyncio
    async def test(
        self, export_limit: int, number_of_pages_per_space: int
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_export_limit(export_limit)
                .with_base_url()
                .with_spaces()
                .with_spaces_pages(number_of_pages_per_space)
            )
            .on_confluence_client_url()
            .on_confluence_client_get_all_spaces()
            .on_confluence_client_get_all_pages_from_space()
        )
        service = manager.get_service()

        # Act
        documents = await service.get_all_documents_async()

        # Assert
        manager.assertions.assert_documents(documents)
