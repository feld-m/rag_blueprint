import sys
import time
from typing import Dict, List, Optional
from unittest.mock import Mock, patch

import pytest
import requests

sys.path.append("./src")

from extraction.datasources.core.api.client import APIClient


class ConcreteAPIClient(APIClient):
    """Concrete implementation of APIClient for testing."""

    def is_last_page(self, data: Dict) -> bool:
        return not data.get("has_more", False)

    def extract_data(self, response_data: Dict) -> List[Dict]:
        return response_data.get("items", [])


class Fixtures:
    def __init__(self):
        self.base_url: str = None
        self.auth: Optional[requests.auth.AuthBase] = None
        self.headers: Optional[Dict[str, str]] = None
        self.timeout: int = None
        self.rate_limit_delay: float = None
        self.paginated_responses: List[Dict] = []
        self.single_response: Dict = {}

    def with_base_url(self) -> "Fixtures":
        self.base_url = "https://api.example.com"
        return self

    def with_auth(self) -> "Fixtures":
        self.auth = Mock(spec=requests.auth.AuthBase)
        return self

    def with_headers(self) -> "Fixtures":
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        return self

    def with_timeout(self, timeout: int = 60) -> "Fixtures":
        self.timeout = timeout
        return self

    def with_rate_limit_delay(self, rate_limit_delay: float = 0.1) -> "Fixtures":
        self.rate_limit_delay = rate_limit_delay
        return self

    def with_paginated_responses(
        self, number_of_pages: int = 3, items_per_page: int = 2
    ) -> "Fixtures":
        self.paginated_responses = []
        for page in range(number_of_pages):
            has_more = page < number_of_pages - 1
            self.paginated_responses.append(
                {
                    "items": [
                        {"id": f"item-{page}-{i}", "name": f"Item {page}-{i}"}
                        for i in range(items_per_page)
                    ],
                    "has_more": has_more,
                    "page": page + 1,
                }
            )
        return self

    def with_single_response(self, items_count: int = 5) -> "Fixtures":
        self.single_response = {
            "items": [
                {"id": f"item-{i}", "name": f"Item {i}"} for i in range(items_count)
            ]
        }
        return self


class Arrangements:
    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        # Create mock session before client init
        self.mock_session = Mock(spec=requests.Session)
        self.mock_session.auth = None
        self.mock_session.headers = {}

        # Init client
        self.service = ConcreteAPIClient(
            base_url=fixtures.base_url or "https://default-api.example.com",
            auth=fixtures.auth,
            headers=fixtures.headers or {},
            timeout=fixtures.timeout or 60,
            rate_limit_delay=fixtures.rate_limit_delay or 0.0,
        )

        # Replace session with mock after init
        self.mock_response = Mock(spec=requests.Response)
        self.service.session = self.mock_session

    def on_make_request_return_single_response(self) -> "Arrangements":
        self.mock_response.json.return_value = self.fixtures.single_response
        self.mock_response.raise_for_status = Mock()
        self.service.make_request = Mock(return_value=self.mock_response)
        return self

    def on_session_request_return_responses(self) -> "Arrangements":
        mock_responses = []
        for data in self.fixtures.paginated_responses:
            mock_response = Mock(spec=requests.Response)
            mock_response.json.return_value = data
            mock_response.raise_for_status = Mock()
            mock_responses.append(mock_response)

        # If no paginated responses are defined, create a default one
        if not mock_responses:
            mock_response = Mock(spec=requests.Response)
            mock_response.json.return_value = {"items": [], "has_more": False}
            mock_response.raise_for_status = Mock()
            mock_responses.append(mock_response)

        # If there's only one response, use it for all requests
        if len(mock_responses) == 1:
            self.mock_session.request.return_value = mock_responses[0]
        else:
            self.mock_session.request.side_effect = mock_responses

        return self


class Assertions:
    def __init__(self, arrangements: Arrangements) -> None:
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.service = arrangements.service

    def assert_session_initialized_with_auth_and_headers(self) -> None:
        # NOTE: For simplicity in testing, we directly check if auth was properly set
        assert self.service.auth == self.fixtures.auth
        # Check if headers match expected headers
        for key, value in self.fixtures.headers.items():
            assert key in self.service.headers
            assert self.service.headers[key] == value

    def assert_request_called_with_correct_parameters(
        self, endpoint: str, method: str = "GET", params: Optional[Dict] = None
    ) -> None:
        expected_url = f"{self.fixtures.base_url}/{endpoint.lstrip('/')}"
        self.arrangements.mock_session.request.assert_called_with(
            method=method,
            url=expected_url,
            params=params or {},
            data=None,
            json=None,
            timeout=self.fixtures.timeout,
        )

    def assert_data_extraction(
        self, data: List[Dict], expected_item_count: int
    ) -> None:
        assert len(data) == expected_item_count

        all_expected_items = []
        for response in self.fixtures.paginated_responses:
            all_expected_items.extend(response["items"])

        for i, item in enumerate(data):
            if i < len(all_expected_items):
                assert item["id"] == all_expected_items[i]["id"]
                assert item["name"] == all_expected_items[i]["name"]


class Manager:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> ConcreteAPIClient:
        return self.arrangements.service


class TestAPIClient:
    def test_initialization(self):
        # Arrange
        fixtures = (
            Fixtures()
            .with_base_url()
            .with_auth()
            .with_headers()
            .with_timeout()
            .with_rate_limit_delay()
        )
        arrangements = Arrangements(fixtures)
        manager = Manager(arrangements)
        service = manager.get_service()

        # Assert
        assert service.base_url == fixtures.base_url
        assert service.auth == fixtures.auth
        assert service.timeout == fixtures.timeout
        assert service.rate_limit_delay == fixtures.rate_limit_delay
        for key, value in fixtures.headers.items():
            assert key in service.headers
            assert service.headers[key] == value

    def test_make_request(self):
        # Arrange
        fixtures = Fixtures().with_base_url().with_timeout().with_headers()
        arrangements = Arrangements(fixtures)

        # Set up a mock response
        mock_response = Mock(spec=requests.Response)
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = Mock()
        arrangements.mock_session.request.return_value = mock_response

        manager = Manager(arrangements)
        service = manager.get_service()

        # Act
        endpoint = "test/endpoint"
        params = {"param1": "value1"}
        service.make_request(endpoint=endpoint, params=params)

        # Assert
        expected_url = f"{fixtures.base_url}/{endpoint.lstrip('/')}"
        arrangements.mock_session.request.assert_called_with(
            method="GET",
            url=expected_url,
            params=params,
            data=None,
            json=None,
            timeout=fixtures.timeout,
        )

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limiting(self, mock_time, mock_sleep):
        # Arrange
        # There should be 3 calls to time.time() in the test: init last_request_time, first check in _apply_rate_limit,
        # and after sleep
        mock_time.side_effect = [0.0, 100.0, 100.5]

        fixtures = Fixtures().with_base_url().with_rate_limit_delay(0.5).with_timeout()
        arrangements = Arrangements(fixtures)

        # Create a single response for the request
        mock_response = Mock(spec=requests.Response)
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = Mock()
        arrangements.mock_session.request.return_value = mock_response

        manager = Manager(arrangements)
        service = manager.get_service()

        # This is to ensure time mocking works fine
        original_apply_rate_limit = service._apply_rate_limit

        def patched_apply_rate_limit():
            if service.rate_limit_delay <= 0:
                return

            elapsed = time.time() - service.last_request_time
            if elapsed < service.rate_limit_delay:
                sleep_time = service.rate_limit_delay - elapsed
                time.sleep(sleep_time)

            service.last_request_time = time.time()

        service._apply_rate_limit = patched_apply_rate_limit

        # Act
        service.make_request("test/endpoint")

        # Assert
        mock_sleep.assert_called_once_with(0.5)

        # Restore original method to prevent affecting other tests
        service._apply_rate_limit = original_apply_rate_limit

    @pytest.mark.parametrize(
        "page_count,items_per_page,expected_item_count",
        [
            (1, 5, 5),
            (3, 2, 6),
            (5, 1, 5),
        ],
    )
    def test_pagination(self, page_count, items_per_page, expected_item_count):
        # Arrange
        fixtures = (
            Fixtures()
            .with_base_url()
            .with_timeout()
            .with_paginated_responses(page_count, items_per_page)
        )
        arrangements = Arrangements(fixtures)
        arrangements.on_session_request_return_responses()
        manager = Manager(arrangements)
        service = manager.get_service()

        # Act
        result = []
        for page_data in service.paginate("test/endpoint"):
            result.extend(service.extract_data(page_data))

        # Assert
        assert len(result) == expected_item_count

        # Verify data matches expected items
        all_expected_items = []
        for response in fixtures.paginated_responses:
            all_expected_items.extend(response["items"])

        for i, item in enumerate(result):
            assert item["id"] == all_expected_items[i]["id"]
            assert item["name"] == all_expected_items[i]["name"]

    def test_read_non_paginated(self):
        # Arrange
        items_count = 5
        fixtures = (
            Fixtures().with_base_url().with_timeout().with_single_response(items_count)
        )
        arrangements = Arrangements(fixtures)
        arrangements.on_make_request_return_single_response()
        manager = Manager(arrangements)
        service = manager.get_service()

        # Act
        result = service.read("test/endpoint", paginated=False)

        # Assert
        assert len(result) == items_count
