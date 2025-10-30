import sys
from typing import Any, Dict, List
from unittest.mock import Mock

import pytest

sys.path.append("./src")

from extraction.datasources.bundestag.client import BundestagMineClient
from extraction.datasources.bundestag.configuration import (
    BundestagMineDatasourceConfiguration,
)
from extraction.datasources.bundestag.reader import (
    BundestagMineDatasourceReader,
)


class Fixtures:
    def __init__(self):
        self.export_limit: int = None
        self.speeches: List[Dict[str, Any]] = []

    def with_export_limit(self, export_limit: int) -> "Fixtures":
        self.export_limit = export_limit
        return self

    def with_speeches(self, number_of_speeches: int) -> "Fixtures":
        for i in range(number_of_speeches):
            speech = {
                "id": f"speech_{i}",
                "speakerId": f"speaker_{i}",
                "text": f"This is speech {i}",
                "speaker": {
                    "firstName": f"FirstName{i}",
                    "lastName": f"LastName{i}",
                    "faction": f"Faction{i % 3}",
                },
            }
            self.speeches.append(speech)
        return self


class Arrangements:
    def __init__(self, fixtures: Fixtures):
        self.fixtures = fixtures
        self.configuration = Mock(spec=BundestagMineDatasourceConfiguration)
        self.configuration.export_limit = self.fixtures.export_limit
        self.configuration.include_bundestag_mine = True
        self.configuration.include_dip = False
        self.client = Mock(spec=BundestagMineClient)
        self.service = BundestagMineDatasourceReader(
            configuration=self.configuration, client=self.client
        )

    def on_client_fetch_all_speeches(self) -> "Arrangements":
        self.client.fetch_all_speeches.return_value = self.fixtures.speeches
        return self


class Assertions:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.service = arrangements.service
        self.client = arrangements.client

    def assert_client_called(self) -> "Assertions":
        self.client.fetch_all_speeches.assert_called_once()
        return self

    def assert_speeches_count(
        self, speeches: List[Dict[str, Any]]
    ) -> "Assertions":
        expected_count = min(
            len(self.fixtures.speeches),
            (
                self.fixtures.export_limit
                if self.fixtures.export_limit is not None
                else float("inf")
            ),
        )
        assert len(speeches) == expected_count
        return self

    def assert_speeches_content(
        self, speeches: List[Dict[str, Any]]
    ) -> "Assertions":
        expected_speeches = self.fixtures.speeches[: self.fixtures.export_limit]
        for expected, actual in zip(expected_speeches, speeches):
            assert actual == expected
        return self


class Manager:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> BundestagMineDatasourceReader:
        return self.arrangements.service


class TestBundestagReader:
    @pytest.mark.parametrize(
        "export_limit,number_of_speeches",
        [
            (5, 10),
            (10, 5),
            (None, 8),
            (None, 440),
            (0, 5),
            (20, 440),
        ],
    )
    @pytest.mark.asyncio
    async def test_read_all_async(
        self, export_limit: int, number_of_speeches: int
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_export_limit(export_limit)
                .with_speeches(number_of_speeches)
            ).on_client_fetch_all_speeches()
        )
        service = manager.get_service()

        # Act
        speeches = []
        async for speech in service.read_all_async():
            speeches.append(speech)

        # Assert
        manager.assertions.assert_client_called()
        manager.assertions.assert_speeches_count(speeches)
        manager.assertions.assert_speeches_content(speeches)
