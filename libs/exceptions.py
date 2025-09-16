"""Custom exceptions for the billing test suite."""

from __future__ import annotations

from typing import Any


class BillingTestException(Exception):
    """Base exception for billing test suite."""


class APIRequestException(BillingTestException):
    """Exception raised when API request fails."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class ValidationException(BillingTestException):
    """Exception raised for validation errors."""



class ConfigurationException(BillingTestException):
    """Exception raised for configuration errors."""



class TimeoutException(BillingTestException):
    """Exception raised when operation times out."""



class AuthenticationException(BillingTestException):
    """Exception raised for authentication failures."""



class ResourceNotFoundException(BillingTestException):
    """Exception raised when requested resource is not found."""



class DuplicateResourceException(BillingTestException):
    """Exception raised when attempting to create duplicate resource."""

