"""Unit tests for HTTP client module following pytest best practices."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

from libs.http_client import (
    BillingAPIClient, 
    RetryConfig,
    HTTPMethod,
    TelemetryManager,
    retry_on_exception,
    SendDataSession
)
from libs.exceptions import APIRequestException, ErrorCode, ErrorContext
from libs.constants import HTTPStatus


class TestBillingAPIClientUnit:
    """Unit tests for BillingAPIClient class."""
    
    @pytest.fixture
    def mock_session(self):
        """Provide a mock session."""
        session = Mock(spec=requests.Session)
        session.headers = {}
        return session
    
    @pytest.fixture
    def api_client(self, mock_session):
        """Provide a test API client with mocked session."""
        client = BillingAPIClient("https://api.example.com", timeout=30)
        # Replace session with mock
        client._session = mock_session
        return client
    
    @pytest.fixture
    def retry_config(self):
        """Provide test retry configuration."""
        return RetryConfig(
            total=5,
            backoff_factor=0.5,
            status_forcelist=(500, 502, 503),
            allowed_methods=("GET", "POST")
        )
    
    # Initialization tests
    def test_init(self):
        """Test BillingAPIClient initialization."""
        client = BillingAPIClient("https://api.example.com", timeout=30)
        
        assert client.base_url == "https://api.example.com"
        assert client.timeout == 30
        assert isinstance(client.retry_config, RetryConfig)
        assert not client.use_mock
    
    def test_init_with_mock(self):
        """Test initialization with mock mode."""
        client = BillingAPIClient("https://api.example.com", use_mock=True)
        
        assert client.base_url == "http://localhost:5000"
        assert client.use_mock
    
    def test_init_with_custom_retry_config(self, retry_config):
        """Test initialization with custom retry configuration."""
        client = BillingAPIClient(
            "https://api.example.com",
            retry_config=retry_config
        )
        
        assert client.retry_config == retry_config
        assert client.retry_config.total == 5
    
    # Context manager tests
    def test_context_manager(self, mock_session):
        """Test context manager functionality."""
        with BillingAPIClient("https://api.example.com") as client:
            client._session = mock_session
            assert client.session == mock_session
        
        # Session should be closed after exiting context
        mock_session.close.assert_called_once()
    
    # URL building tests
    def test_build_url(self, api_client):
        """Test URL building."""
        # Simple endpoint
        url = api_client._build_url("/api/v1/billing")
        assert url == "https://api.example.com/api/v1/billing"
        
        # Endpoint without leading slash
        url = api_client._build_url("api/v1/billing")
        assert url == "https://api.example.com/api/v1/billing"
        
        # With query parameters
        url = api_client._build_url("/api/v1/billing", {"page": 1, "size": 10})
        assert "page=1" in url
        assert "size=10" in url
    
    # Response validation tests
    def test_validate_response_success(self, api_client):
        """Test successful response validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "header": {"isSuccessful": True},
            "data": {"result": "success"}
        }
        
        result = api_client._validate_response(mock_response)
        assert result == mock_response.json.return_value
    
    def test_validate_response_invalid_json(self, api_client):
        """Test response validation with invalid JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.headers = {"content-type": "application/json"}
        
        with pytest.raises(APIRequestException) as exc_info:
            api_client._validate_response(mock_response)
        
        assert "Invalid JSON" in str(exc_info.value)
        assert exc_info.value.status_code == 200
    
    def test_validate_response_http_error(self, api_client):
        """Test response validation with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}
        
        with pytest.raises(APIRequestException) as exc_info:
            api_client._validate_response(mock_response)
        
        assert exc_info.value.status_code == 404
        assert "HTTP 404" in str(exc_info.value)
    
    def test_validate_response_api_error(self, api_client):
        """Test response validation with API-specific error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "header": {
                "isSuccessful": False,
                "resultMessage": "Invalid request"
            }
        }
        
        with pytest.raises(APIRequestException) as exc_info:
            api_client._validate_response(mock_response)
        
        assert "API error: Invalid request" in str(exc_info.value)
    
    # Request method tests
    @patch('libs.http_client.TelemetryManager')
    def test_request_success(self, mock_telemetry_cls, api_client, mock_session):
        """Test successful request."""
        # Setup mocks
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_session.request.return_value = mock_response
        
        # Make request
        result = api_client.request(HTTPMethod.GET, "/test")
        
        # Verify
        assert result == {"result": "success"}
        mock_session.request.assert_called_once_with(
            method="GET",
            url="https://api.example.com/test",
            headers=mock_session.headers,
            params=None,
            json=None,
            data=None,
            timeout=30
        )
    
    def test_request_with_params(self, api_client, mock_session):
        """Test request with query parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_session.request.return_value = mock_response
        
        params = {"page": 1, "size": 10}
        api_client.request(HTTPMethod.GET, "/test", params=params)
        
        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args.kwargs["params"] == params
    
    def test_request_with_json_data(self, api_client, mock_session):
        """Test request with JSON data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_session.request.return_value = mock_response
        
        json_data = {"key": "value"}
        api_client.request(HTTPMethod.POST, "/test", json_data=json_data)
        
        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args.kwargs["json"] == json_data
    
    def test_request_exception_handling(self, api_client, mock_session):
        """Test request exception handling."""
        mock_session.request.side_effect = ConnectionError("Connection failed")
        
        with pytest.raises(APIRequestException) as exc_info:
            api_client.request(HTTPMethod.GET, "/test")
        
        assert "Request failed: Connection failed" in str(exc_info.value)
    
    # Convenience method tests
    def test_get_method(self, api_client):
        """Test GET convenience method."""
        with patch.object(api_client, 'request') as mock_request:
            mock_request.return_value = {"result": "success"}
            
            result = api_client.get("/test", params={"key": "value"})
            
            assert result == {"result": "success"}
            mock_request.assert_called_once_with(
                HTTPMethod.GET,
                "/test",
                params={"key": "value"}
            )
    
    def test_post_method(self, api_client):
        """Test POST convenience method."""
        with patch.object(api_client, 'request') as mock_request:
            mock_request.return_value = {"result": "success"}
            
            result = api_client.post("/test", json_data={"key": "value"})
            
            assert result == {"result": "success"}
            mock_request.assert_called_once_with(
                HTTPMethod.POST,
                "/test",
                json_data={"key": "value"}
            )
    
    # Wait for completion tests
    def test_wait_for_completion_success(self, api_client):
        """Test successful wait for completion."""
        with patch.object(api_client, 'get') as mock_get:
            # First call: not complete
            # Second call: complete
            mock_get.side_effect = [
                {"status": "PENDING"},
                {"status": "COMPLETED", "result": "success"}
            ]
            
            result = api_client.wait_for_completion(
                "/status",
                status_field="status",
                success_value="COMPLETED",
                timeout=10,
                check_interval=0.1
            )
            
            assert result == {"status": "COMPLETED", "result": "success"}
            assert mock_get.call_count == 2
    
    def test_wait_for_completion_timeout(self, api_client):
        """Test wait for completion timeout."""
        with patch.object(api_client, 'get') as mock_get:
            mock_get.return_value = {"status": "PENDING"}
            
            with pytest.raises(APIRequestException) as exc_info:
                api_client.wait_for_completion(
                    "/status",
                    timeout=0.2,
                    check_interval=0.1
                )
            
            assert "Operation timed out" in str(exc_info.value)
    
    def test_wait_for_completion_with_callback(self, api_client):
        """Test wait for completion with progress callback."""
        callback_calls = []
        
        def progress_callback(response):
            callback_calls.append(response)
        
        with patch.object(api_client, 'get') as mock_get:
            mock_get.side_effect = [
                {"status": "PENDING", "progress": 50},
                {"status": "COMPLETED", "progress": 100}
            ]
            
            api_client.wait_for_completion(
                "/status",
                status_field="status",
                success_value="COMPLETED",
                progress_callback=progress_callback,
                check_interval=0.1
            )
            
            # Should have at least one callback (the pending status)
            assert len(callback_calls) >= 1
            assert callback_calls[0]["progress"] == 50
            # If we have a second callback, it should be the completed status
            if len(callback_calls) > 1:
                assert callback_calls[-1]["progress"] == 100


class TestRetryDecorator:
    """Unit tests for retry decorator."""
    
    def test_retry_on_exception_success(self):
        """Test retry decorator with eventual success."""
        call_count = 0
        
        @retry_on_exception(max_retries=3, backoff_factor=0.1)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = flaky_function()
        
        assert result == "success"
        assert call_count == 2
    
    def test_retry_on_exception_all_failures(self):
        """Test retry decorator with all attempts failing."""
        call_count = 0
        
        @retry_on_exception(max_retries=3, backoff_factor=0.1)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Permanent failure")
        
        with pytest.raises(ConnectionError) as exc_info:
            always_fails()
        
        assert "Permanent failure" in str(exc_info.value)
        assert call_count == 3


class TestTelemetryManager:
    """Unit tests for TelemetryManager class."""
    
    def test_telemetry_disabled(self):
        """Test telemetry when not available."""
        manager = TelemetryManager()
        
        # Should handle gracefully when telemetry not available
        with manager.span("test.operation", {"key": "value"}) as span:
            assert span is None
        
        # Record should not raise
        manager.record_api_call(endpoint="/test", method="GET", status_code=200)
    
    @patch('libs.observability.get_telemetry')
    def test_telemetry_enabled(self, mock_get_telemetry):
        """Test telemetry when available."""
        mock_telemetry = Mock()
        mock_span = Mock()
        mock_telemetry.create_span.return_value = mock_span
        mock_get_telemetry.return_value = mock_telemetry
        
        # Create manager and manually enable telemetry
        manager = TelemetryManager()
        manager._telemetry = mock_telemetry
        manager._enabled = True
        
        with manager.span("test.operation", {"key": "value"}) as span:
            assert span == mock_span
        
        mock_telemetry.create_span.assert_called_once_with(
            "test.operation",
            key="value"
        )
        mock_span.end.assert_called_once()


class TestSendDataSession:
    """Unit tests for backward compatibility wrapper."""
    
    def test_legacy_wrapper_initialization(self):
        """Test legacy wrapper initialization."""
        with pytest.warns(DeprecationWarning):
            session = SendDataSession("GET", "https://api.example.com/test")
        
        assert session.method == "GET"
        assert session.url == "https://api.example.com/test"
        assert session._endpoint == "/test"
    
    def test_legacy_wrapper_properties(self):
        """Test legacy wrapper property setters/getters."""
        with pytest.warns(DeprecationWarning):
            session = SendDataSession("POST", "https://api.example.com/test")
        
        # Test property setters
        session.data = "test data"
        session.json = {"key": "value"}
        session.headers = {"Content-Type": "application/json"}
        
        # Test property getters
        assert session.data == "test data"
        assert session.json == {"key": "value"}
        assert session.headers == {"Content-Type": "application/json"}
    
    @patch('libs.http_client.BillingAPIClient')
    def test_legacy_wrapper_request(self, mock_client_cls):
        """Test legacy wrapper request method."""
        mock_client = Mock()
        mock_client.request.return_value = {"result": "success"}
        mock_client_cls.return_value = mock_client
        
        with pytest.warns(DeprecationWarning):
            session = SendDataSession("POST", "https://api.example.com/test")
        
        session.json = {"key": "value"}
        response = session.request()
        
        assert response.json() == {"result": "success"}