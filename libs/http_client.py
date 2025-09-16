"""HTTP client for billing API interactions."""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .constants import (
    DEFAULT_CHECK_INTERVAL,
    DEFAULT_RETRY_COUNT,
    DEFAULT_TIMEOUT,
    HEADER_MESSAGE_KEY,
    HEADER_SUCCESS_KEY,
)
from .exceptions import APIRequestException

logger = logging.getLogger(__name__)


class BillingAPIClient:
    """HTTP client for billing API requests with retry and error handling."""

    def __init__(
        self,
        base_url: str,
        timeout: int = DEFAULT_TIMEOUT,
        retry_count: int = DEFAULT_RETRY_COUNT,
    ) -> None:
        """Initialize API client.

        Args:
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
            retry_count: Number of retries for failed requests
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = self._create_session(retry_count)

    def _create_session(self, retry_count: int) -> requests.Session:
        """Create session with retry strategy."""
        session = requests.Session()

        retry_strategy = Retry(
            total=retry_count,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        return urljoin(self.base_url, endpoint)

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """Handle API response and check for errors.

        Args:
            response: Raw response from API

        Returns:
            Response data as dictionary

        Raises:
            APIRequestException: If response indicates failure
        """
        try:
            data = response.json()
        except ValueError as e:
            msg = f"Invalid JSON response: {e}"
            raise APIRequestException(
                msg, status_code=response.status_code
            )

        # Check if response indicates success
        if response.status_code >= 400:
            msg = f"API request failed with status {response.status_code}"
            raise APIRequestException(
                msg,
                status_code=response.status_code,
                response_data=data,
            )

        # Check API-specific success indicator
        header = data.get("header", {})
        if not header.get(HEADER_SUCCESS_KEY, False):
            message = header.get(HEADER_MESSAGE_KEY, "Unknown error")
            msg = f"API returned error: {message}"
            raise APIRequestException(
                msg, response_data=data
            )

        return data

    def request(
        self,
        method: str,
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        data: str | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            headers: Optional request headers
            params: Optional query parameters
            json_data: Optional JSON body data
            data: Optional form data

        Returns:
            Response data

        Raises:
            APIRequestException: If request fails
        """
        url = self._build_url(endpoint)

        # Prepare headers
        request_headers = {"Accept": "application/json;charset=UTF-8"}
        if headers:
            request_headers.update(headers)

        logger.debug("Making {method} request to %s", url)

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                json=json_data,
                data=data,
                timeout=self.timeout,
            )

            return self._handle_response(response)

        except requests.RequestException as e:
            logger.exception("Request failed: %s", e)
            msg = f"Request failed: {e}"
            raise APIRequestException(msg)

    def get(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make GET request."""
        return self.request("GET", endpoint, headers=headers, params=params)

    def post(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
        data: str | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make POST request."""
        return self.request(
            "POST", endpoint, headers=headers, json_data=json_data, data=data
        )

    def put(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make PUT request."""
        return self.request("PUT", endpoint, headers=headers, json_data=json_data)

    def delete(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make DELETE request."""
        return self.request("DELETE", endpoint, headers=headers, params=params)

    def wait_for_completion(
        self,
        check_endpoint: str,
        completion_field: str,
        max_field: str,
        progress_code: str,
        check_interval: int = DEFAULT_CHECK_INTERVAL,
        max_wait_time: int = 300,
    ) -> bool:
        """Wait for an async operation to complete.

        Args:
            check_endpoint: Endpoint to check progress
            completion_field: Field name for current progress
            max_field: Field name for maximum progress
            progress_code: Code to match in response
            check_interval: Seconds between checks
            max_wait_time: Maximum seconds to wait

        Returns:
            True if completed, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                response = self.get(check_endpoint)

                # Find matching progress entry
                for entry in response.get("list", []):
                    if entry.get("batchJobCode") == progress_code:
                        current = entry.get(completion_field, 0)
                        maximum = entry.get(max_field, 0)

                        logger.debug("Progress: {current}/%s", maximum)

                        if maximum > 0 and current >= maximum:
                            return True
                        break

            except APIRequestException as e:
                logger.warning("Progress check failed: %s", e)

            time.sleep(check_interval)

        return False


# Backward compatibility wrapper
class SendDataSession:
    """Legacy wrapper for backward compatibility."""

    def __init__(self, method: str, url: str) -> None:
        self.method = method
        self.url = url
        self._data = ""
        self._json = {}
        self._headers = {}

        # Extract base URL from full URL
        from urllib.parse import urlparse

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        endpoint = parsed.path
        if parsed.query:
            endpoint += f"?{parsed.query}"

        self._client = BillingAPIClient(base_url)
        self._endpoint = endpoint

    def __repr__(self) -> str:
        return (
            f"Session(method: {self.method}, requestUrl: {self.url}, "
            f"data: {self.data}, json: {self.json}, headers: {self.headers})"
        )

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data) -> None:
        self._data = data

    @property
    def json(self):
        return self._json

    @json.setter
    def json(self, json) -> None:
        self._json = json

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers) -> None:
        self._headers = headers

    def request(self, **kwargs):
        """Make request using new client."""
        response_data = self._client.request(
            method=self.method,
            endpoint=self._endpoint,
            headers=self.headers if self.headers else None,
            json_data=self.json if self.json else None,
            data=self.data if self.data else None,
        )

        # Create mock response object for backward compatibility
        class MockResponse:
            def json(self):
                return response_data

        return MockResponse()
