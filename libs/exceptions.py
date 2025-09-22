"""
Custom exceptions for the billing test suite.

This module provides a comprehensive exception hierarchy for handling
various error conditions in the billing system.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional, Union


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
    
    # Business logic errors (6xxx)
    PAYMENT_FAILED = 6000
    CREDIT_INSUFFICIENT = 6001
    CONTRACT_VIOLATED = 6002
    
    # System errors (9xxx)
    INTERNAL_ERROR = 9000
    SERVICE_UNAVAILABLE = 9001


@dataclass
class ErrorContext:
    """Additional context information for errors."""
    
    error_code: ErrorCode
    details: Dict[str, Any]
    retry_after: Optional[int] = None  # Seconds to wait before retry
    is_retryable: bool = False
    suggested_action: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
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
    """
    Base exception for billing test suite.
    
    All custom exceptions in the billing system should inherit from this class.
    It provides common functionality for error handling and reporting.
    """
    
    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """
        Initialize the exception.
        
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
            parts.append(f"Caused by: {type(self.cause).__name__}: {str(self.cause)}")
        
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
    def error_code(self) -> Optional[ErrorCode]:
        """Get the error code if context is available."""
        return self.context.error_code if self.context else None
    
    @property
    def is_retryable(self) -> bool:
        """Check if the error is retryable."""
        return self.context.is_retryable if self.context else False


class APIRequestException(BillingTestException):
    """
    Exception raised when API request fails.
    
    This exception includes additional information about the HTTP response
    such as status code and response data.
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """
        Initialize API request exception.
        
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
                retry_after=self._extract_retry_after(response_data)
            )
        
        super().__init__(message, context, cause)
        self.status_code = status_code
        self.response_data = response_data
    
    def _determine_error_code(self, status_code: int) -> ErrorCode:
        """Determine error code based on status code."""
        if status_code == 429:
            return ErrorCode.API_RATE_LIMITED
        elif status_code >= 500:
            return ErrorCode.SERVICE_UNAVAILABLE
        elif status_code == 408:
            return ErrorCode.API_TIMEOUT
        else:
            return ErrorCode.API_REQUEST_FAILED
    
    def _extract_retry_after(self, response_data: Optional[Dict[str, Any]]) -> Optional[int]:
        """Extract retry-after value from response."""
        if not response_data:
            return None
        
        # Check common locations for retry-after
        return response_data.get("retry_after") or response_data.get("retryAfter")


class ValidationException(BillingTestException):
    """
    Exception raised for validation errors.
    
    Used when input data fails validation rules.
    """
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        invalid_value: Any = None,
        context: Optional[ErrorContext] = None
    ) -> None:
        """
        Initialize validation exception.
        
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
                is_retryable=False
            )
        
        super().__init__(message, context)
        self.field_name = field_name
        self.invalid_value = invalid_value


class ConfigurationException(BillingTestException):
    """
    Exception raised for configuration errors.
    
    Used when configuration is missing, invalid, or cannot be loaded.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ) -> None:
        """
        Initialize configuration exception.
        
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
                suggested_action="Check configuration files and environment variables"
            )
        
        super().__init__(message, context)
        self.config_key = config_key


class TimeoutException(BillingTestException):
    """
    Exception raised when operation times out.
    
    Used for operations that exceed their time limit.
    """
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ) -> None:
        """
        Initialize timeout exception.
        
        Args:
            message: Error message
            timeout_seconds: Timeout duration in seconds
            operation: Name of the operation that timed out
            context: Error context
        """
        if context is None:
            details = {}
            if timeout_seconds:
                details["timeout_seconds"] = timeout_seconds
            if operation:
                details["operation"] = operation
            
            context = ErrorContext(
                error_code=ErrorCode.API_TIMEOUT,
                details=details,
                is_retryable=True,
                suggested_action="Increase timeout or retry the operation"
            )
        
        super().__init__(message, context)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class AuthenticationException(BillingTestException):
    """
    Exception raised for authentication failures.
    
    Used when authentication or authorization fails.
    """
    
    def __init__(
        self,
        message: str,
        auth_method: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ) -> None:
        """
        Initialize authentication exception.
        
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
                suggested_action="Check credentials and authentication configuration"
            )
        
        super().__init__(message, context)
        self.auth_method = auth_method


class ResourceNotFoundException(BillingTestException):
    """
    Exception raised when requested resource is not found.
    
    Used for 404-type errors.
    """
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ) -> None:
        """
        Initialize resource not found exception.
        
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
                suggested_action="Verify the resource ID and ensure it exists"
            )
        
        super().__init__(message, context)
        self.resource_type = resource_type
        self.resource_id = resource_id


class DuplicateResourceException(BillingTestException):
    """
    Exception raised when attempting to create duplicate resource.
    
    Used when a unique constraint is violated.
    """
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ) -> None:
        """
        Initialize duplicate resource exception.
        
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
                suggested_action="Use a different identifier or update the existing resource"
            )
        
        super().__init__(message, context)
        self.resource_type = resource_type
        self.resource_id = resource_id


class BusinessLogicException(BillingTestException):
    """
    Exception raised for business logic violations.
    
    Used when business rules are violated.
    """
    
    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ) -> None:
        """
        Initialize business logic exception.
        
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
                is_retryable=False
            )
        
        super().__init__(message, context)
        self.rule_name = rule_name


# Utility functions for exception handling
def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable.
    
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


def get_retry_after(error: Exception) -> Optional[int]:
    """
    Get the retry-after value from an error.
    
    Args:
        error: The exception to check
        
    Returns:
        Number of seconds to wait before retry, or None
    """
    if isinstance(error, BillingTestException) and error.context:
        return error.context.retry_after
    
    return None