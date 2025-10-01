"""Security features for mock server: rate limiting and authentication."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable

from flask import Request, Response, g, jsonify, request


class RateLimiter:
    """Simple in-memory rate limiter for testing."""

    def __init__(self, max_requests: int = 50, window_seconds: int = 1) -> None:
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_id(self) -> str:
        """Get unique client identifier."""
        # Use UUID from header if available, otherwise IP
        return request.headers.get("uuid") or request.remote_addr or "unknown"

    def _clean_old_requests(self, client_id: str, current_time: float) -> None:
        """Remove requests outside the time window."""
        cutoff_time = current_time - self.window_seconds
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id] if req_time > cutoff_time
        ]

    def is_rate_limited(self) -> bool:
        """Check if current request should be rate limited."""
        client_id = self._get_client_id()
        current_time = time.time()

        # Clean old requests
        self._clean_old_requests(client_id, current_time)

        # Check rate limit
        if len(self.requests[client_id]) >= self.max_requests:
            return True

        # Add current request
        self.requests[client_id].append(current_time)
        return False

    def get_remaining_requests(self) -> int:
        """Get remaining requests in current window."""
        client_id = self._get_client_id()
        current_time = time.time()
        self._clean_old_requests(client_id, current_time)
        return max(0, self.max_requests - len(self.requests[client_id]))


# Global rate limiter instance
# For integration tests, use higher limit (500 req/sec)
# For security tests, use lower limit (50 req/sec)
_max_requests = int(os.environ.get("MOCK_SERVER_RATE_LIMIT", "500"))
rate_limiter = RateLimiter(max_requests=_max_requests, window_seconds=1)


def rate_limit_middleware(app: Any) -> None:
    """Add rate limiting middleware to Flask app."""

    @app.before_request
    def check_rate_limit() -> tuple[Response, int] | None:
        """Check rate limit before processing request."""
        # Skip rate limit check for health and docs endpoints
        if request.path in ["/health", "/docs", "/", "/openapi.json", "/openapi.yaml"]:
            return None

        if rate_limiter.is_rate_limited():
            return (
                jsonify(
                    {
                        "header": {
                            "isSuccessful": False,
                            "resultCode": 429,
                            "resultMessage": "Too many requests - rate limit exceeded",
                        },
                        "error": "RATE_LIMIT_EXCEEDED",
                        "retry_after": rate_limiter.window_seconds,
                        "remaining_requests": 0,
                    }
                ),
                429,
            )

        # Add rate limit info to response headers
        g.rate_limit_remaining = rate_limiter.get_remaining_requests()
        return None

    @app.after_request
    def add_rate_limit_headers(response: Any) -> Any:
        """Add rate limit headers to response."""
        if hasattr(g, "rate_limit_remaining"):
            response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(g.rate_limit_remaining)
            response.headers["X-RateLimit-Reset"] = str(
                int(time.time() + rate_limiter.window_seconds)
            )
        return response


def validate_uuid(uuid_value: str) -> tuple[bool, str | None]:
    """Validate UUID for security issues.

    Args:
        uuid_value: UUID string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not uuid_value:
        return False, "UUID is required"

    # Check for malicious patterns
    malicious_patterns = [
        "'",
        '"',
        ";",
        "--",
        "/*",
        "*/",  # SQL injection
        "<",
        ">",
        "<script",
        "<iframe",  # XSS
        "..",
        "\\",  # Path traversal
        "\n",
        "\r",
        "\0",  # Control characters
    ]

    for pattern in malicious_patterns:
        if pattern in uuid_value:
            return (
                False,
                f"Invalid UUID format: contains forbidden character/pattern '{pattern}'",
            )

    # Check length (UUIDs are typically 36 chars with dashes, or custom format up to 100)
    if len(uuid_value) > 100:
        return False, "UUID too long"

    # Check if only contains safe characters (alphanumeric, dash, underscore)
    if not all(c.isalnum() or c in ["-", "_"] for c in uuid_value):
        return False, "UUID contains invalid characters"

    return True, None


def require_valid_uuid(f: Callable) -> Callable:
    """Decorator to require and validate UUID in request headers."""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        uuid_value = request.headers.get("uuid")

        # Check if UUID is provided
        if not uuid_value:
            return (
                jsonify(
                    {
                        "header": {
                            "isSuccessful": False,
                            "resultCode": 401,
                            "resultMessage": "Authentication failed: UUID required",
                        },
                        "error": "MISSING_UUID",
                    }
                ),
                401,
            )

        # Validate UUID
        is_valid, error_message = validate_uuid(uuid_value)
        if not is_valid:
            return (
                jsonify(
                    {
                        "header": {
                            "isSuccessful": False,
                            "resultCode": 400,
                            "resultMessage": f"Invalid UUID: {error_message}",
                        },
                        "error": "INVALID_UUID",
                    }
                ),
                400,
            )

        return f(*args, **kwargs)

    return decorated_function


def validate_request_headers(
    request_obj: Request,
) -> tuple[bool, dict[str, Any] | None]:
    """Validate request headers for security.

    Args:
        request_obj: Flask request object

    Returns:
        Tuple of (is_valid, error_response)
    """
    # Check UUID in header for authenticated endpoints
    uuid_value = request_obj.headers.get("uuid")

    if uuid_value:
        is_valid, error_message = validate_uuid(uuid_value)
        if not is_valid:
            return False, {
                "header": {
                    "isSuccessful": False,
                    "resultCode": 400,
                    "resultMessage": f"Invalid UUID: {error_message}",
                },
                "error": "INVALID_UUID",
            }

    # Check for header injection attempts
    dangerous_headers = ["X-Forwarded-For", "X-Real-IP"]
    for header in dangerous_headers:
        value = request_obj.headers.get(header, "")
        if any(char in value for char in ["\n", "\r", ";", ","]):
            return False, {
                "header": {
                    "isSuccessful": False,
                    "resultCode": 400,
                    "resultMessage": f"Invalid header value: {header}",
                },
                "error": "INVALID_HEADER",
            }

    return True, None


def setup_security(app: Any) -> None:
    """Setup security features for Flask app.

    Args:
        app: Flask application instance
    """
    # Add rate limiting
    rate_limit_middleware(app)

    # Add header validation
    @app.before_request
    def validate_headers() -> tuple[Response, int] | None:
        """Validate request headers before processing."""
        # Skip validation for public endpoints
        public_paths = [
            "/health",
            "/docs",
            "/",
            "/openapi.json",
            "/openapi.yaml",
            "/test/reset",
            "/pact-states",
        ]

        if request.path in public_paths or request.path.startswith("/docs/"):
            return None

        is_valid, error_response = validate_request_headers(request)
        if not is_valid:
            return jsonify(error_response), 400

        return None
