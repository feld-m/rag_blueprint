import abc
import logging
import time
from typing import Any, Dict, Iterator, List, Optional

import requests
from requests.auth import AuthBase

logger = logging.getLogger(__name__)


class APIClient(abc.ABC):
    """Base class for API data extraction."""

    def __init__(
        self,
        base_url: str,
        auth: Optional[AuthBase] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 60,
        rate_limit_delay: float = 0.0,
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API.
            auth: Authentication method for requests.
            headers: HTTP headers to include in requests.
            timeout: Request timeout in seconds.
            rate_limit_delay: Delay between requests in seconds (0 = no rate limiting).
        """
        self.base_url = base_url
        self.auth = auth
        self.headers = headers or {}
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0.0
        self.session = requests.Session()
        if auth:
            self.session.auth = auth
        self.session.headers.update(self.headers)

    def _apply_rate_limit(self):
        """Apply rate limiting by enforcing a delay between requests."""
        if self.rate_limit_delay <= 0:
            return

        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Make an HTTP request to the API.

        Args:
            endpoint: API endpoint to call.
            method: HTTP method (GET, POST, etc.).
            params: URL parameters.
            data: Form data.
            json_data: JSON data.

        Returns:
            Response object.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Apply rate limiting before making the request
        self._apply_rate_limit()

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_param: str = "page",
        limit_param: str = "limit",
        limit: int = 100,
        max_pages: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Handle paginated API responses.

        Args:
            endpoint: API endpoint to call.
            params: Initial URL parameters.
            page_param: Name of the pagination parameter.
            limit_param: Name of the limit parameter.
            limit: Number of items per page.
            max_pages: Maximum number of pages to retrieve.

        Yields:
            Data from each page of results.
        """
        params = params or {}
        params.update({limit_param: limit, page_param: 1})
        page = 1

        while True:
            response = self.make_request(endpoint, params=params)
            data = response.json()

            if not data:
                break

            yield data

            if max_pages and page >= max_pages:
                break

            page += 1
            params[page_param] = page

            # Break if the API indicates no more pages
            if self.is_last_page(data):
                break

    @abc.abstractmethod
    def is_last_page(self, data: Dict[str, Any]) -> bool:
        """
        Determine if this is the last page of results.

        Args:
            data: Current page data.

        Returns:
            True if this is the last page, False otherwise.
        """
        pass

    @abc.abstractmethod
    def extract_data(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract relevant data from API response.

        Args:
            response_data: API response data.

        Returns:
            Extracted data items.
        """
        pass

    def read(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        paginated: bool = False,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Read data from the API.

        Args:
            endpoint: API endpoint to call.
            method: HTTP method.
            params: URL parameters.
            paginated: Whether to handle pagination.
            **kwargs: Additional arguments for pagination.

        Returns:
            List of data items.
        """
        results = []

        if paginated:
            for page_data in self.paginate(endpoint, params=params, **kwargs):
                results.extend(self.extract_data(page_data))
        else:
            response = self.make_request(endpoint, method=method, params=params)
            results.extend(self.extract_data(response.json()))

        return results
