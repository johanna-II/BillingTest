"""Custom exceptions for the billing test suite.

This module provides a comprehensive exception hierarchy for handling
various error conditions in the billing system.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorCode(Enum):
    """Standardized error codes for the billing system."""

    # API errors (1xxx)
    API_REQUEST_FAILED = 1000
    API_TIMEOUT = 1001
    API_RATE_LIMITED = 1002
    API_INVALID_RESPONSE = 1003

    # Validation errors (2xxx)
    VALIDATION_FAILED = 2000
    INVALID_DATE_FORMAT = 2001
    INVALID_AMOUNT = 2002
    INVALID_STATUS = 2003
    MISSING_REQUIRED_FIELD = 2004

    # Configuration errors (3xxx)
    CONFIG_NOT_FOUND = 3000
    CONFIG_INVALID = 3001
    CONFIG_MISSING_FIELD = 3002

    # Authentication errors (4xxx)
    AUTH_FAILED = 4000
    AUTH_TOKEN_EXPIRED = 4001
    AUTH_INSUFFICIENT_PERMISSIONS = 4002

    # Resource errors (5xxx)
    RESOURCE_NOT_FOUND = 5000
    RESOURCE_ALREADY_EXISTS = 5001
    RESOURCE_LOCKED = 5002
    DUPLICATE_REQUEST = 5003

    # Business logic errors (6xxx)
    PAYMENT_FAILED = 6000
    CREDIT_INSUFFICIENT = 6001
    CONTRACT_VIOLATED = 6002
    PAYMENT_REQUIRED = 6003
    INSUFFICIENT_CREDIT = 6004

    # Network errors (7xxx)
    NETWORK_ERROR = 7000
    CONNECTION_TIMEOUT = 7001

    # Rate limiting (8xxx)
    RATE_LIMIT_EXCEEDED = 8000

    # System errors (9xxx)
    INTERNAL_ERROR = 9000
    SERVICE_UNAVAILABLE = 9001


@dataclass
class ErrorContext:
    """Additional context information for errors."""

    error_code: ErrorCode
    details: dict[str, Any]
    retry_after: int | None = None  # Seconds to wait before retry
    is_retryable: bool = False
    suggested_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "error_code": self.error_code.name,
            "error_code_value": self.error_code.value,
            "details": self.details,
            "retry_after": self.retry_after,
            "is_retryable": self.is_retryable,
            "suggested_action": self.suggested_action,
        }


class BillingTestException(Exception):
    """Base exception for billing test suite.

    All custom exceptions in the billing system should inherit from this class.
    It provides common functionality for error handling and reporting.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message
            context: Additional error context
            cause: The underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.context = context
        self.cause = cause

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]

        if self.context:
            parts.append(f"[{self.context.error_code.name}]")
            if self.context.suggested_action:
                parts.append(f"Suggestion: {self.context.suggested_action}")

        if self.cause:
            parts.append(f"Caused by: {type(self.cause).__name__}: {self.cause!s}")

        return " | ".join(parts)

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.context.error_code if self.context else None}, "
            f"is_retryable={self.context.is_retryable if self.context else False})"
        )

    @property
    def error_code(self) -> ErrorCode | None:
        """Get the error code if context is available."""
        return self.context.error_code if self.context else None

    @property
    def is_retryable(self) -> bool:
        """Check if the error is retryable."""
        return self.context.is_retryable if self.context else False


class APIRequestException(BillingTestException):
    """Exception raised when API request fails.

    This exception includes additional information about the HTTP response
    such as status code and response data.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
        context: ErrorContext | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize API request exception.

        Args:
            message: Error message
            status_code: HTTP status code
            response_data: Response body data
            context: Error context
            cause: Underlying exception
        """
        # Auto-determine if retryable based on status code
        if context is None and status_code:
            is_retryable = status_code >= 500 or status_code == 429
            error_code = self._determine_error_code(status_code)

            context = ErrorContext(
                error_code=error_code,
                details={"status_code": status_code, "response": response_data},
                is_retryable=is_retryable,
                retry_after=self._extract_retry_after(response_data),
            )

        super().__init__(message, context, cause)
        self.status_code = status_code
        self.response_data = response_data

    def _determine_error_code(self, status_code: int) -> ErrorCode:
        """Determine error code based on status code."""
        if status_code == 429:
            return ErrorCode.API_RATE_LIMITED
        if status_code >= 500:
            return ErrorCode.SERVICE_UNAVAILABLE
        if status_code == 408:
            return ErrorCode.API_TIMEOUT
        return ErrorCode.API_REQUEST_FAILED

    def _extract_retry_after(self, response_data: dict[str, Any] | None) -> int | None:
        """Extract retry-after value from response."""
        if not response_data:
            return None

        # Check common locations for retry-after
        return response_data.get("retry_after") or response_data.get("retryAfter")


class ValidationException(BillingTestException):
    """Exception raised for validation errors.

    Used when input data fails validation rules.
    """

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        invalid_value: Any = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize validation exception.

        Args:
            message: Error message
            field_name: Name of the invalid field
            invalid_value: The invalid value
            context: Error context
        """
        if context is None:
            details = {}
            if field_name:
                details["field"] = field_name
            if invalid_value is not None:
                details["value"] = str(invalid_value)

            context = ErrorContext(
                error_code=ErrorCode.VALIDATION_FAILED,
                details=details,
                is_retryable=False,
            )

        super().__init__(message, context)
        self.field_name = field_name
        self.invalid_value = invalid_value


class ConfigurationException(BillingTestException):
    """Exception raised for configuration errors.

    Used when configuration is missing, invalid, or cannot be loaded.
    """

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize configuration exception.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
            context: Error context
        """
        if context is None:
            details = {}
            if config_key:
                details["config_key"] = config_key

            context = ErrorContext(
                error_code=ErrorCode.CONFIG_INVALID,
                details=details,
                is_retryable=False,
                suggested_action="Check configuration files and environment variables",
            )

        super().__init__(message, context)
        self.config_key = config_key


class TimeoutException(BillingTestException):
    """Exception raised when operation times out.

    Used for operations that exceed their time limit.
    """

    def __init__(
        self,
        message: str,
        timeout_seconds: float | None = None,
        operation: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize timeout exception.

        Args:
            message: Error message
            timeout_seconds: Timeout duration in seconds
            operation: Name of the operation that timed out
            context: Error context
        """
        if context is None:
            details: dict[str, Any] = {}
            if timeout_seconds:
                details["timeout_seconds"] = timeout_seconds
            if operation:
                details["operation"] = operation

            context = ErrorContext(
                error_code=ErrorCode.API_TIMEOUT,
                details=details,
                is_retryable=True,
                suggested_action="Increase timeout or retry the operation",
            )

        super().__init__(message, context)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class AuthenticationException(BillingTestException):
    """Exception raised for authentication failures.

    Used when authentication or authorization fails.
    """

    def __init__(
        self,
        message: str,
        auth_method: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize authentication exception.

        Args:
            message: Error message
            auth_method: Authentication method that failed
            context: Error context
        """
        if context is None:
            details = {}
            if auth_method:
                details["auth_method"] = auth_method

            context = ErrorContext(
                error_code=ErrorCode.AUTH_FAILED,
                details=details,
                is_retryable=False,
                suggested_action="Check credentials and authentication configuration",
            )

        super().__init__(message, context)
        self.auth_method = auth_method


class ResourceNotFoundException(BillingTestException):
    """Exception raised when requested resource is not found.

    Used for 404-type errors.
    """

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize resource not found exception.

        Args:
            message: Error message
            resource_type: Type of resource (e.g., 'payment', 'credit')
            resource_id: ID of the missing resource
            context: Error context
        """
        if context is None:
            details = {}
            if resource_type:
                details["resource_type"] = resource_type
            if resource_id:
                details["resource_id"] = resource_id

            context = ErrorContext(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                details=details,
                is_retryable=False,
                suggested_action="Verify the resource ID and ensure it exists",
            )

        super().__init__(message, context)
        self.resource_type = resource_type
        self.resource_id = resource_id


class DuplicateResourceException(BillingTestException):
    """Exception raised when attempting to create duplicate resource.

    Used when a unique constraint is violated.
    """

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize duplicate resource exception.

        Args:
            message: Error message
            resource_type: Type of resource
            resource_id: ID of the duplicate resource
            context: Error context
        """
        if context is None:
            details = {}
            if resource_type:
                details["resource_type"] = resource_type
            if resource_id:
                details["resource_id"] = resource_id

            context = ErrorContext(
                error_code=ErrorCode.RESOURCE_ALREADY_EXISTS,
                details=details,
                is_retryable=False,
                suggested_action="Use a different identifier or update the existing resource",
            )

        super().__init__(message, context)
        self.resource_type = resource_type
        self.resource_id = resource_id


class BusinessLogicException(BillingTestException):
    """Exception raised for business logic violations.

    Used when business rules are violated.
    """

    def __init__(
        self,
        message: str,
        rule_name: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize business logic exception.

        Args:
            message: Error message
            rule_name: Name of the violated business rule
            context: Error context
        """
        if context is None:
            details = {}
            if rule_name:
                details["rule"] = rule_name

            context = ErrorContext(
                error_code=ErrorCode.CONTRACT_VIOLATED,
                details=details,
                is_retryable=False,
            )

        super().__init__(message, context)
        self.rule_name = rule_name


# Utility functions for exception handling
def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable.

    Args:
        error: The exception to check

    Returns:
        True if the error is retryable, False otherwise
    """
    if isinstance(error, BillingTestException):
        return error.is_retryable

    # Check for common retryable errors
    retryable_types = (ConnectionError, TimeoutError)
    return isinstance(error, retryable_types)


def get_retry_after(error: Exception) -> int | None:
    """Get the retry-after value from an error.

    Args:
        error: The exception to check

    Returns:
        Number of seconds to wait before retry, or None
    """
    if isinstance(error, BillingTestException) and error.context:
        return error.context.retry_after

    return None


class ConflictException(BillingTestException):
    """Exception raised when a resource conflict occurs."""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        conflict_reason: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize conflict exception.

        Args:
            message: Error message
            resource_type: Type of resource in conflict
            conflict_reason: Reason for the conflict
            context: Error context
        """
        if context is None:
            details = {}
            if resource_type:
                details["resource_type"] = resource_type
            if conflict_reason:
                details["conflict_reason"] = conflict_reason

            context = ErrorContext(
                error_code=ErrorCode.DUPLICATE_REQUEST,
                details=details,
                is_retryable=False,
                suggested_action="Resolve the conflict or use a different resource",
            )

        super().__init__(message, context)
        self.resource_type = resource_type
        self.conflict_reason = conflict_reason


class RateLimitException(BillingTestException):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        limit: int | None = None,
        reset_time: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize rate limit exception.

        Args:
            message: Error message
            limit: The rate limit that was exceeded
            reset_time: When the rate limit will reset
            context: Error context
        """
        if context is None:
            details: dict[str, Any] = {}
            if limit:
                details["limit"] = limit
            if reset_time:
                details["reset_time"] = reset_time

            context = ErrorContext(
                error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
                details=details,
                is_retryable=True,
                retry_after=60,  # Default to 60 seconds
                suggested_action="Wait before retrying the request",
            )

        super().__init__(message, context)
        self.limit = limit
        self.reset_time = reset_time


class ServerException(BillingTestException):
    """Exception raised for server-side errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize server exception.

        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Server error code
            context: Error context
        """
        if context is None:
            details: dict[str, Any] = {}
            if status_code:
                details["status_code"] = status_code
            if error_code:
                details["error_code"] = error_code

            context = ErrorContext(
                error_code=ErrorCode.INTERNAL_ERROR,
                details=details,
                is_retryable=True,
                suggested_action="Contact support if the error persists",
            )

        super().__init__(message, context)
        self.status_code = status_code
        self.server_error_code = error_code


class NetworkException(BillingTestException):
    """Exception raised for network-related errors."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        cause: Exception | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize network exception.

        Args:
            message: Error message
            operation: The operation that failed
            cause: The underlying exception that caused the network failure
            context: Error context
        """
        if context is None:
            details: dict[str, Any] = {}
            if operation:
                details["operation"] = operation
            if cause:
                details["cause"] = str(cause)

            context = ErrorContext(
                error_code=ErrorCode.NETWORK_ERROR,
                details=details,
                is_retryable=True,
                suggested_action="Check network connectivity and retry",
            )

        super().__init__(message, context, cause)
        self.operation = operation
        self.network_cause = cause


class PaymentRequiredException(BillingTestException):
    """Exception raised when payment is required."""

    def __init__(
        self,
        message: str,
        required_amount: float | None = None,
        currency: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize payment required exception.

        Args:
            message: Error message
            required_amount: Amount required for payment
            currency: Currency of the required payment
            context: Error context
        """
        if context is None:
            details: dict[str, Any] = {}
            if required_amount:
                details["required_amount"] = required_amount
            if currency:
                details["currency"] = currency

            context = ErrorContext(
                error_code=ErrorCode.PAYMENT_REQUIRED,
                details=details,
                is_retryable=False,
                suggested_action="Complete payment to proceed",
            )

        super().__init__(message, context)
        self.required_amount = required_amount
        self.currency = currency


class InsufficientCreditException(BillingTestException):
    """Exception raised when there is insufficient credit."""

    def __init__(
        self,
        message: str,
        required_amount: float | None = None,
        available_amount: float | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize insufficient credit exception.

        Args:
            message: Error message
            required_amount: Amount of credit required
            available_amount: Amount of credit available
            context: Error context
        """
        if context is None:
            details = {}
            if required_amount:
                details["required_amount"] = required_amount
            if available_amount:
                details["available_amount"] = available_amount

            context = ErrorContext(
                error_code=ErrorCode.INSUFFICIENT_CREDIT,
                details=details,
                is_retryable=False,
                suggested_action="Add more credit or reduce usage",
            )

        super().__init__(message, context)
        self.required_amount = required_amount
        self.available_amount = available_amount
