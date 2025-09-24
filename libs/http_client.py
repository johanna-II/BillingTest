"""HTTP client for billing API interactions with retry and telemetry support."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, Self, TypeVar, Union
from urllib.parse import urlencode, urljoin, urlparse

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

if TYPE_CHECKING:
    from requests.models import Response

# Type aliases for clarity
Headers = dict[str, str]
Params = dict[str, Any]
JsonData = dict[str, Any]
RequestData = Union[str, dict[str, Any]]

# Generic type for decorated functions
F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


class HTTPMethod(str, Enum):
    """HTTP methods enum for type safety."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    total: int = DEFAULT_RETRY_COUNT
    backoff_factor: float = 1.0
    status_forcelist: tuple[int, ...] = (500, 502, 503, 504)
    allowed_methods: tuple[str, ...] = ("GET", "POST", "PUT", "DELETE", "PATCH")
    respect_retry_after_header: bool = True


@dataclass
class APIResponse:
    """Structured API response with metadata."""

    data: JsonData
    status_code: int
    headers: Headers
    elapsed_ms: float

    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return 200 <= self.status_code < 300


class TelemetryManager:
    """Manages telemetry integration."""

    def __init__(self) -> None:
        self._telemetry = None
        self._enabled = False
        self._initialize_telemetry()

    def _initialize_telemetry(self) -> None:
        """Try to initialize telemetry if available."""
        try:
            from .observability import get_telemetry

            self._telemetry = get_telemetry()
            self._enabled = True
        except ImportError:
            logger.debug("Telemetry not available")

    @contextmanager
    def span(self, operation: str, attributes: dict[str, Any]):
        """Context manager for telemetry spans."""
        if not self._enabled or not self._telemetry:
            yield None
            return

        span = self._telemetry.create_span(operation, attributes=attributes)
        try:
            yield span
        except Exception as e:
            if span:
                span.record_exception(e)
                # Set error status on span
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
            raise
        finally:
            if span:
                span.end()

    def record_api_call(self, **kwargs) -> None:
        """Record API call metrics."""
        if self._enabled and self._telemetry:
            self._telemetry.record_api_call(**kwargs)


def retry_on_exception(
    exceptions: tuple[type, ...] = (requests.RequestException,),
    max_retries: int = 3,
    backoff_factor: float = 1.0,
) -> Callable[[F], F]:
    """Decorator for retrying functions on specific exceptions."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor * (2**attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.exception(f"All {max_retries} attempts failed")

            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


class BillingAPIClient:
    """HTTP client for billing API requests with retry and error handling.

    Implements connection pooling, automatic retries, and telemetry integration.
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = DEFAULT_TIMEOUT,
        retry_config: RetryConfig | None = None,
        use_mock: bool = False,
    ) -> None:
        """Initialize API client.

        Args:
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
            retry_config: Optional retry configuration
            use_mock: Whether to use mock server (localhost:5000)
        """
        self.base_url = "http://localhost:5000" if use_mock else base_url
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.use_mock = use_mock

        self._session: requests.Session | None = None
        self._telemetry = TelemetryManager()

        # Initialize session
        self._setup_session()

    def _setup_session(self) -> None:
        """Set up requests session with retry strategy."""
        self._session = requests.Session()

        retry_strategy = Retry(
            total=self.retry_config.total,
            backoff_factor=self.retry_config.backoff_factor,
            status_forcelist=list(self.retry_config.status_forcelist),
            allowed_methods=list(self.retry_config.allowed_methods),
            respect_retry_after_header=self.retry_config.respect_retry_after_header,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

        # Set default headers
        self._session.headers.update(
            {
                "Accept": "application/json;charset=UTF-8",
                "User-Agent": "BillingAPIClient/1.0",
            }
        )

    @property
    def session(self) -> requests.Session:
        """Get the current session, creating if necessary."""
        if self._session is None:
            self._setup_session()
        return self._session

    def close(self) -> None:
        """Close the session and release resources."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close session."""
        self.close()

    def _build_url(self, endpoint: str, params: Params | None = None) -> str:
        """Build full URL from endpoint and parameters.

        Args:
            endpoint: API endpoint path
            params: Optional query parameters

        Returns:
            Full URL with query parameters
        """
        # Remove leading slash to avoid double slashes
        endpoint = endpoint.lstrip("/")
        url = urljoin(self.base_url, endpoint)

        if params:
            # Filter out None values and encode parameters
            filtered_params = {k: v for k, v in params.items() if v is not None}
            if filtered_params:
                query_string = urlencode(filtered_params, doseq=True)
                url = f"{url}?{query_string}"

        return url

    def _validate_response(self, response: Response) -> JsonData:
        """Validate and parse API response.

        Args:
            response: Raw response from API

        Returns:
            Parsed response data

        Raises:
            APIRequestException: If response indicates failure
        """
        # Try to parse JSON response
        try:
            data = response.json()
        except ValueError as e:
            # For non-JSON responses, check if it's expected
            if response.headers.get("content-type", "").startswith("text/"):
                return {"text": response.text}

            msg = f"Invalid JSON response: {e}"
            raise APIRequestException(msg, status_code=response.status_code)

        # Check HTTP status code
        if response.status_code >= 400:
            error_msg = self._extract_error_message(data, response.status_code)
            raise APIRequestException(
                error_msg, status_code=response.status_code, response_data=data
            )

        # Check API-specific success indicator
        if isinstance(data, dict):
            header = data.get("header", {})
            if header and not header.get(HEADER_SUCCESS_KEY, True):
                message = header.get(HEADER_MESSAGE_KEY, "Unknown API error")
                msg = f"API error: {message}"
                raise APIRequestException(msg, response_data=data)

        return data

    def _extract_error_message(self, data: Any, status_code: int) -> str:
        """Extract error message from response data."""
        if isinstance(data, dict):
            # Try common error message fields
            for field in ["error", "message", "detail", "error_message"]:
                if field in data:
                    return f"HTTP {status_code}: {data[field]}"

            # Check nested header
            if "header" in data and isinstance(data["header"], dict):
                if HEADER_MESSAGE_KEY in data["header"]:
                    return f"HTTP {status_code}: {data['header'][HEADER_MESSAGE_KEY]}"

        return f"HTTP {status_code}: Request failed"

    def request(
        self,
        method: str | HTTPMethod,
        endpoint: str,
        headers: Headers | None = None,
        params: Params | None = None,
        json_data: JsonData | None = None,
        data: RequestData | None = None,
        **kwargs: Any,
    ) -> JsonData:
        """Make HTTP request to API.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            headers: Optional request headers
            params: Optional query parameters
            json_data: Optional JSON body data
            data: Optional form data
            **kwargs: Additional arguments passed to requests

        Returns:
            Response data

        Raises:
            APIRequestException: If request fails
        """
        # Validate method
        method = HTTPMethod(method.upper()) if isinstance(method, str) else method

        # Build URL without params (they'll be passed separately)
        url = self._build_url(endpoint)

        # Merge headers
        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)

        # Log request details
        logger.debug(
            f"Making {method.value} request to {endpoint} "
            f"(params: {len(params or {})}, "
            f"json: {'yes' if json_data else 'no'}, "
            f"data: {'yes' if data else 'no'})"
        )

        # Prepare telemetry attributes
        parsed_url = urlparse(url)
        telemetry_attrs = {
            "http.method": method.value,
            "http.url": url,
            "http.host": parsed_url.netloc,
            "http.path": parsed_url.path,
            "http.scheme": parsed_url.scheme,
        }

        start_time = time.time()

        with self._telemetry.span(
            f"http.{method.value.lower()}", telemetry_attrs
        ) as span:
            try:
                response = self.session.request(
                    method=method.value,
                    url=url,
                    headers=request_headers,
                    params=params,
                    json=json_data,
                    data=data,
                    timeout=self.timeout,
                    **kwargs,
                )

                elapsed_ms = (time.time() - start_time) * 1000

                # Update telemetry
                if span:
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_attribute("http.response_time_ms", elapsed_ms)

                self._telemetry.record_api_call(
                    endpoint=parsed_url.path,
                    method=method.value,
                    status_code=response.status_code,
                    response_time=elapsed_ms / 1000,  # Convert back to seconds
                )

                # Validate and return response
                return self._validate_response(response)

            except requests.RequestException as e:
                logger.exception(f"Request failed: {e}")
                msg = f"Request failed: {e}"
                raise APIRequestException(msg)

    # Convenience methods for common HTTP verbs
    def get(self, endpoint: str, **kwargs) -> JsonData:
        """Make GET request."""
        return self.request(HTTPMethod.GET, endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> JsonData:
        """Make POST request."""
        return self.request(HTTPMethod.POST, endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> JsonData:
        """Make PUT request."""
        return self.request(HTTPMethod.PUT, endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> JsonData:
        """Make DELETE request."""
        return self.request(HTTPMethod.DELETE, endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> JsonData:
        """Make PATCH request."""
        return self.request(HTTPMethod.PATCH, endpoint, **kwargs)

    def wait_for_completion(
        self,
        check_endpoint: str,
        *,
        status_field: str = "status",
        success_value: str = "COMPLETED",
        timeout: int = 300,
        check_interval: int = DEFAULT_CHECK_INTERVAL,
        progress_callback: Callable[[JsonData], None] | None = None,
    ) -> JsonData:
        """Wait for an async operation to complete.

        Args:
            check_endpoint: Endpoint to check status
            status_field: Field name containing status
            success_value: Value indicating completion
            timeout: Maximum seconds to wait
            check_interval: Seconds between checks
            progress_callback: Optional callback for progress updates

        Returns:
            Final response data

        Raises:
            APIRequestException: If operation fails or times out
        """
        start_time = time.time()
        last_response = None

        while time.time() - start_time < timeout:
            try:
                response = self.get(check_endpoint)
                last_response = response

                # Check if completed
                if self._check_completion(response, status_field, success_value):
                    logger.info("Operation completed successfully")
                    return response

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(response)

            except APIRequestException as e:
                logger.warning(f"Status check failed: {e}")

            # Wait before next check
            remaining_time = timeout - (time.time() - start_time)
            wait_time = min(check_interval, remaining_time)
            if wait_time > 0:
                time.sleep(wait_time)

        # Timeout reached
        msg = f"Operation timed out after {timeout}s"
        raise APIRequestException(msg, response_data=last_response)

    def _check_completion(
        self, response: JsonData, status_field: str, success_value: str
    ) -> bool:
        """Check if response indicates completion."""
        # Handle nested status fields (e.g., "result.status")
        current = response
        for field in status_field.split("."):
            if isinstance(current, dict) and field in current:
                current = current[field]
            else:
                return False

        return current == success_value

    def set_auth_token(self, token: str) -> None:
        """Set authorization token for all requests."""
        self.session.headers["Authorization"] = f"Bearer {token}"

    def clear_auth_token(self) -> None:
        """Remove authorization token."""
        self.session.headers.pop("Authorization", None)
