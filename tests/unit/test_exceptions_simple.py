"""Simple tests for exceptions module."""

import pytest
from libs.exceptions import (
    APIRequestException,
    ValidationException,
    BillingTestException,
    ConfigurationException,
    TimeoutException,
    AuthenticationException,
    ResourceNotFoundException,
    DuplicateResourceException,
    BusinessLogicException
)


class TestExceptionsSimple:
    """Simple tests for exception classes."""
    
    def test_api_request_exception(self):
        """Test APIRequestException."""
        exc = APIRequestException("API error occurred")
        assert "API error" in str(exc)
        assert isinstance(exc, BillingTestException)
    
    def test_validation_exception(self):
        """Test ValidationException."""
        exc = ValidationException("Invalid value")
        assert "Invalid value" in str(exc)
        assert isinstance(exc, BillingTestException)
    
    def test_configuration_exception(self):
        """Test ConfigurationException."""
        exc = ConfigurationException("Config error")
        assert "Config error" in str(exc)
        assert isinstance(exc, BillingTestException)
    
    def test_timeout_exception(self):
        """Test TimeoutException."""
        exc = TimeoutException("Request timed out")
        assert "timed out" in str(exc)
        assert isinstance(exc, BillingTestException)
    
    def test_authentication_exception(self):
        """Test AuthenticationException."""
        exc = AuthenticationException("Auth failed")
        assert "Auth failed" in str(exc)
        assert isinstance(exc, BillingTestException)
    
    def test_resource_not_found_exception(self):
        """Test ResourceNotFoundException."""
        exc = ResourceNotFoundException("Resource not found")
        assert "not found" in str(exc)
        assert isinstance(exc, BillingTestException)
    
    def test_duplicate_resource_exception(self):
        """Test DuplicateResourceException."""
        exc = DuplicateResourceException("Duplicate resource")
        assert "Duplicate" in str(exc)
        assert isinstance(exc, BillingTestException)
    
    def test_business_logic_exception(self):
        """Test BusinessLogicException."""
        exc = BusinessLogicException("Business rule violation")
        assert "Business" in str(exc)
        assert isinstance(exc, BillingTestException)
    
    def test_billing_test_exception_base(self):
        """Test base BillingTestException."""
        exc = BillingTestException("Base error")
        assert "Base error" in str(exc)
        assert isinstance(exc, Exception)
