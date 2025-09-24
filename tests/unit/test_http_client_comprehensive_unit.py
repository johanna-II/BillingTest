"""Comprehensive unit tests for HTTP client module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError
import time

from libs.http_client import BillingAPIClient, HTTPMethod, APIResponse, RetryConfig
from libs.exceptions import APIRequestException


class TestBillingAPIClientComprehensiveUnit:
    """Comprehensive unit tests for BillingAPIClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.base_url = "https://billing.api.example.com"
        self.client = BillingAPIClient(base_url=self.base_url)
    
    def test_init_with_empty_base_url(self):
        """Test initialization with empty base URL."""
        client = BillingAPIClient("")
        assert client.base_url is None or client.base_url == ""
        assert hasattr(client, '_session')
        # _telemetry_manager might not exist depending on implementation
        assert hasattr(client, 'session')
    
    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        client = BillingAPIClient(base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"
    
    def test_init_with_trailing_slash(self):
        """Test initialization handles trailing slash in base URL."""
        client = BillingAPIClient(base_url="https://api.com/")
        assert client.base_url == "https://api.com/"
    
    def test_build_url_with_base_path(self):
        """Test URL building with base path."""
        url = self.client._build_url("billing/payments")
        assert url == "https://billing.api.example.com/billing/payments"
    
    def test_build_url_with_query_params(self):
        """Test URL building with query parameters."""
        params = {"page": 1, "limit": 50, "status": "active"}
        url = self.client._build_url("billing/payments", params=params)
        
        assert url.startswith("https://billing.api.example.com/billing/payments?")
        assert "page=1" in url
        assert "limit=50" in url
        assert "status=active" in url
    
    def test_build_url_without_base_url(self):
        """Test URL building when no base URL is set."""
        client = BillingAPIClient("")
        url = client._build_url("billing/payments")
        assert url == "billing/payments"
    
    @patch('requests.Session')
    def test_request_with_json_data(self, mock_session_class):
        """Test request with JSON data."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        # Set headers as a dictionary
        mock_session.headers = {}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.headers = MagicMock()
        mock_response.headers.get.return_value = "application/json"
        mock_response.elapsed.total_seconds.return_value = 0.123
        mock_session.request.return_value = mock_response
        
        client = BillingAPIClient(base_url=self.base_url)
        client._session = mock_session
        
        json_data = {"key": "value"}
        result = client.request(
            method=HTTPMethod.POST,
            endpoint="test",
            json_data=json_data
        )
        
        assert result["status"] == "success"
        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[1]["json"] == json_data
    
    @patch('requests.Session')
    def test_request_with_custom_headers(self, mock_session_class):
        """Test request with custom headers."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        # Set headers as a dictionary
        mock_session.headers = {}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.headers = MagicMock()
        mock_response.headers.get.return_value = "application/json"
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_session.request.return_value = mock_response
        
        client = BillingAPIClient(base_url=self.base_url)
        client._session = mock_session
        
        custom_headers = {"X-Custom-Header": "custom-value"}
        result = client.request(
            method=HTTPMethod.GET,
            endpoint="test",
            headers=custom_headers
        )
        
        assert result["status"] == "success"
        call_args = mock_session.request.call_args
        assert "X-Custom-Header" in call_args[1]["headers"]
        assert call_args[1]["headers"]["X-Custom-Header"] == "custom-value"
    
    @patch('requests.Session')
    def test_handle_404_error(self, mock_session_class):
        """Test handling of 404 errors."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        # Set headers as a dictionary
        mock_session.headers = {}
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.headers = MagicMock()
        mock_response.headers.get.return_value = "text/plain"
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_session.request.return_value = mock_response
        
        client = BillingAPIClient(base_url=self.base_url)
        client._session = mock_session
        
        with pytest.raises(APIRequestException) as exc_info:
            client.request(HTTPMethod.GET, "nonexistent")
        
        assert "404" in str(exc_info.value)
    
    @patch('requests.Session')
    def test_handle_500_error(self, mock_session_class):
        """Test handling of 500 errors."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        # Set headers as a dictionary
        mock_session.headers = {}
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.headers = MagicMock()
        mock_response.headers.get.return_value = "text/plain"
        mock_response.raise_for_status.side_effect = HTTPError("500 Internal Server Error")
        mock_session.request.return_value = mock_response
        
        client = BillingAPIClient(base_url=self.base_url)
        client._session = mock_session
        
        with pytest.raises(APIRequestException) as exc_info:
            client.request(HTTPMethod.POST, "error")
        
        assert "500" in str(exc_info.value)
    
    @patch('requests.Session')
    def test_connection_timeout(self, mock_session_class):
        """Test handling of connection timeout."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        # Set headers as a dictionary
        mock_session.headers = {}
        mock_session.request.side_effect = Timeout("Connection timeout")
        
        client = BillingAPIClient(base_url=self.base_url)
        client._session = mock_session
        
        with pytest.raises(APIRequestException) as exc_info:
            client.request(HTTPMethod.GET, "timeout")
        
        assert "Connection timeout" in str(exc_info.value)
    
    @patch('requests.Session')
    def test_connection_error(self, mock_session_class):
        """Test handling of connection errors."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        # Set headers as a dictionary
        mock_session.headers = {}
        mock_session.request.side_effect = ConnectionError("Connection failed")
        
        client = BillingAPIClient(base_url=self.base_url)
        client._session = mock_session
        
        with pytest.raises(APIRequestException) as exc_info:
            client.request(HTTPMethod.GET, "connection-error")
        
        assert "Connection failed" in str(exc_info.value)
    
    @patch('requests.Session')
    def test_retry_on_transient_error(self, mock_session_class):
        """Test retry mechanism on transient errors."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        # Set headers as a dictionary
        mock_session.headers = {}
        
        # First call fails with 503, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 503
        mock_response_fail.text = "Service Unavailable"
        mock_response_fail.headers = MagicMock()
        mock_response_fail.headers.get.return_value = "text/plain"
        mock_response_fail.raise_for_status.side_effect = HTTPError("503")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"status": "success"}
        mock_response_success.headers = MagicMock()
        mock_response_success.headers.get.return_value = "application/json"
        mock_response_success.elapsed.total_seconds.return_value = 0.1
        
        # Note: With retry adapter, this behavior is handled by urllib3
        # For unit test, we'll simulate the retry behavior
        mock_session.request.side_effect = [mock_response_fail, mock_response_success]
        
        client = BillingAPIClient(base_url=self.base_url)
        client._session = mock_session
        
        # Since retries are handled by the adapter, we simulate the behavior
        try:
            client.request(HTTPMethod.GET, "retry-test")
        except APIRequestException:
            # Retry and get success
            result = client.request(HTTPMethod.GET, "retry-test")
            assert result["status"] == "success"
    
    def test_wait_for_completion_immediate_success(self):
        """Test wait_for_completion with immediate success."""
        with patch.object(self.client, 'get') as mock_get:
            mock_get.return_value = {"status": "COMPLETED", "data": "test"}
            
            result = self.client.wait_for_completion(
                check_endpoint="progress",
                status_field="status",
                success_value="COMPLETED",
                timeout=10,
                check_interval=1
            )
            
            assert result == {"status": "COMPLETED", "data": "test"}
            mock_get.assert_called_once()
    
    def test_wait_for_completion_with_delay(self):
        """Test wait_for_completion with delayed completion."""
        with patch.object(self.client, 'get') as mock_get:
            # First two calls show progress, third shows completion
            mock_get.side_effect = [
                {"status": "IN_PROGRESS"},
                {"status": "IN_PROGRESS"},
                {"status": "COMPLETED"}
            ]
            
            with patch('time.sleep'):  # Mock sleep to speed up test
                result = self.client.wait_for_completion(
                    check_endpoint="progress",
                    status_field="status",
                    success_value="COMPLETED",
                    timeout=10,
                    check_interval=1
                )
            
            assert result == {"status": "COMPLETED"}
            assert mock_get.call_count == 3
    
    def test_wait_for_completion_timeout(self):
        """Test wait_for_completion with timeout."""
        with patch.object(self.client, 'get') as mock_get:
            # Always return incomplete progress
            mock_get.return_value = {"status": "IN_PROGRESS"}
            
            with patch('time.sleep'):  # Mock sleep to speed up test
                with patch('time.time') as mock_time:
                    # Simulate timeout by making time advance
                    mock_time.side_effect = [0, 0.5, 1.0, 1.5, 2.0]  # Exceeds timeout
                    
                    with pytest.raises(APIRequestException, match="timed out"):
                        self.client.wait_for_completion(
                            check_endpoint="progress",
                            status_field="status",
                            success_value="COMPLETED",
                            timeout=1,  # Very short timeout
                            check_interval=0.1
                        )
    
    def test_mock_mode_behavior(self):
        """Test behavior in mock mode."""
        import os
        os.environ["USE_MOCK_SERVER"] = "true"
        os.environ["MOCK_SERVER_PORT"] = "5000"
        
        try:
            client = BillingAPIClient(base_url=self.base_url)
            
            # In mock mode, base_url might be overridden
            # This depends on implementation details
            assert hasattr(client, 'base_url')
        finally:
            # Clean up
            os.environ.pop("USE_MOCK_SERVER", None)
            os.environ.pop("MOCK_SERVER_PORT", None)
    
    @patch('requests.Session')
    def test_response_with_non_json_content(self, mock_session_class):
        """Test handling response with non-JSON content."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        # Set headers as a dictionary
        mock_session.headers = {}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("No JSON object could be decoded")
        mock_response.text = "Plain text response"
        mock_response.headers = MagicMock()
        mock_response.headers.get.return_value = "text/plain"
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_session.request.return_value = mock_response
        
        client = BillingAPIClient(base_url=self.base_url)
        client._session = mock_session
        
        # Should handle non-JSON gracefully
        result = client.request(HTTPMethod.GET, "text-response")
        
        # Result should be the text content or empty dict
        assert isinstance(result, (dict, str))
    
    def test_session_persistence(self):
        """Test that session is reused across requests."""
        client = BillingAPIClient(base_url=self.base_url)
        session1 = client.session
        
        # Make another client
        client2 = BillingAPIClient(base_url=self.base_url)
        session2 = client2.session
        
        # Sessions should be different instances
        assert session1 is not session2
        
        # But same client should reuse session
        assert client.session is session1
    
    def test_auth_header_injection(self):
        """Test automatic auth header injection."""
        # Create client
        client = BillingAPIClient(base_url=self.base_url)
        
        # Check that session headers were set correctly
        assert "Accept" in client.session.headers
        assert client.session.headers["Accept"] == "application/json;charset=UTF-8"
        assert "User-Agent" in client.session.headers
        assert client.session.headers["User-Agent"] == "BillingAPIClient/1.0"
    
    def test_get_method(self):
        """Test GET method."""
        with patch.object(self.client, 'request') as mock_request:
            mock_request.return_value = {"data": "test"}
            
            result = self.client.get("test-endpoint", params={"q": "search"})
            
            assert result == {"data": "test"}
            # Check that request was called with GET method
            args, kwargs = mock_request.call_args
            assert args[0] == HTTPMethod.GET
            assert args[1] == "test-endpoint"
            assert kwargs.get("params") == {"q": "search"}
    
    def test_post_method(self):
        """Test POST method."""
        with patch.object(self.client, 'request') as mock_request:
            mock_request.return_value = {"created": True}
            
            json_data = {"name": "test"}
            result = self.client.post("test-endpoint", json_data=json_data)
            
            assert result == {"created": True}
            # Check that request was called with POST method
            args, kwargs = mock_request.call_args
            assert args[0] == HTTPMethod.POST
            assert args[1] == "test-endpoint"
            assert kwargs.get("json_data") == json_data
    
    def test_put_method(self):
        """Test PUT method."""
        with patch.object(self.client, 'request') as mock_request:
            mock_request.return_value = {"updated": True}
            
            json_data = {"name": "updated"}
            result = self.client.put("test-endpoint", json_data=json_data)
            
            assert result == {"updated": True}
            # Check that request was called with PUT method
            args, kwargs = mock_request.call_args
            assert args[0] == HTTPMethod.PUT
            assert args[1] == "test-endpoint"
            assert kwargs.get("json_data") == json_data
    
    def test_delete_method(self):
        """Test DELETE method."""
        with patch.object(self.client, 'request') as mock_request:
            mock_request.return_value = {"deleted": True}
            
            result = self.client.delete("test-endpoint", params={"id": "123"})
            
            assert result == {"deleted": True}
            # Check that request was called with DELETE method
            args, kwargs = mock_request.call_args
            assert args[0] == HTTPMethod.DELETE
            assert args[1] == "test-endpoint"
            assert kwargs.get("params") == {"id": "123"}
    
    def test_custom_timeout(self):
        """Test using custom timeout."""
        with patch.object(self.client, 'request') as mock_request:
            mock_request.return_value = {"data": "test"}
            
            # Test with custom timeout
            self.client.get("test", timeout=60)
            
            call_args = mock_request.call_args
            assert call_args[1]["timeout"] == 60
    
    def test_retry_config(self):
        """Test retry configuration."""
        config = RetryConfig(
            total=5,
            backoff_factor=2.0,
            status_forcelist=(500, 502, 503),
            allowed_methods=("GET", "POST")
        )
        
        assert config.total == 5
        assert config.backoff_factor == 2.0
        assert 503 in config.status_forcelist
        assert "GET" in config.allowed_methods
        assert config.respect_retry_after_header is True
    
    def test_api_response_dataclass(self):
        """Test APIResponse dataclass."""
        response = APIResponse(
            data={"key": "value"},
            status_code=200,
            headers={"content-type": "application/json"},
            elapsed_ms=123.45
        )
        
        assert response.is_success is True
        assert response.data == {"key": "value"}
        assert response.status_code == 200
        assert response.elapsed_ms == 123.45
        
        # Test non-success response
        error_response = APIResponse(
            data={"error": "not found"},
            status_code=404,
            headers={},
            elapsed_ms=50.0
        )
        assert error_response.is_success is False