"""Unit tests for HTTP Client to improve coverage."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import ConnectionError, Timeout

from libs.http_client import BillingAPIClient, SendDataSession
from libs.exceptions import APIRequestException
from libs.constants import HEADER_SUCCESS_KEY, HEADER_MESSAGE_KEY


class TestBillingAPIClientUnit:
    """Unit tests for BillingAPIClient class."""

    @pytest.fixture
    def mock_session(self):
        """Mock requests session."""
        return Mock(spec=requests.Session)

    @pytest.fixture
    def api_client(self, mock_session):
        """Create BillingAPIClient with mocked session."""
        with patch('libs.http_client.requests.Session', return_value=mock_session):
            client = BillingAPIClient("https://api.example.com", timeout=30, retry_count=3)
            client.session = mock_session
            return client

    def test_init(self):
        """Test BillingAPIClient initialization."""
        client = BillingAPIClient("https://api.example.com")
        assert client.base_url == "https://api.example.com"
        assert client.timeout == 60  # Default timeout
        assert hasattr(client, 'session')

    def test_create_session_with_retry_strategy(self):
        """Test session creation with retry strategy."""
        client = BillingAPIClient("https://api.example.com", retry_count=5)
        
        # Verify session has retry adapter
        assert hasattr(client.session, 'mount')
        # Session should have adapters for both http and https
        assert len(client.session.adapters) >= 2

    def test_build_url(self, api_client):
        """Test URL building."""
        # Test with relative endpoint
        url = api_client._build_url("/api/v1/test")
        assert url == "https://api.example.com/api/v1/test"
        
        # Test without leading slash
        url = api_client._build_url("api/v1/test")
        assert url == "https://api.example.com/api/v1/test"

    def test_handle_response_success(self, api_client):
        """Test successful response handling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "header": {HEADER_SUCCESS_KEY: True},
            "data": {"id": 123}
        }
        
        result = api_client._handle_response(mock_response)
        
        assert result == {
            "header": {HEADER_SUCCESS_KEY: True},
            "data": {"id": 123}
        }

    def test_handle_response_invalid_json(self, api_client):
        """Test handling invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        with pytest.raises(APIRequestException) as exc_info:
            api_client._handle_response(mock_response)
        
        assert "Invalid JSON response" in str(exc_info.value)

    def test_handle_response_http_error(self, api_client):
        """Test handling HTTP error status codes."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}
        
        with pytest.raises(APIRequestException) as exc_info:
            api_client._handle_response(mock_response)
        
        assert exc_info.value.status_code == 404
        assert "API request failed with status 404" in str(exc_info.value)

    def test_handle_response_api_error(self, api_client):
        """Test handling API-specific errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "header": {
                HEADER_SUCCESS_KEY: False,
                HEADER_MESSAGE_KEY: "Insufficient balance"
            }
        }
        
        with pytest.raises(APIRequestException) as exc_info:
            api_client._handle_response(mock_response)
        
        assert "API returned error: Insufficient balance" in str(exc_info.value)

    def test_request_with_telemetry(self, api_client, mock_session):
        """Test request with telemetry enabled."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"header": {HEADER_SUCCESS_KEY: True}}
        mock_session.request.return_value = mock_response
        
        with patch('libs.http_client.get_telemetry') as mock_get_telemetry:
            mock_telemetry = Mock()
            mock_get_telemetry.return_value = mock_telemetry
            
            result = api_client.request("GET", "/test")
            
            mock_telemetry.record_api_call.assert_called_once()

    def test_get_method(self, api_client, mock_session):
        """Test GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"header": {HEADER_SUCCESS_KEY: True}}
        mock_session.request.return_value = mock_response
        
        result = api_client.get("/test", params={"id": 123})
        
        # API client adds Accept header automatically
        expected_headers = {"Accept": "application/json;charset=UTF-8"}
        mock_session.request.assert_called_with(
            method="GET",
            url="https://api.example.com/test",
            headers=expected_headers,
            params={"id": 123},
            json=None,
            data=None,
            timeout=30
        )

    def test_post_method(self, api_client, mock_session):
        """Test POST request."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"header": {HEADER_SUCCESS_KEY: True}}
        mock_session.request.return_value = mock_response
        
        data = {"name": "test", "value": 123}
        result = api_client.post("/test", json_data=data)
        
        # API client adds Accept header automatically
        expected_headers = {"Accept": "application/json;charset=UTF-8"}
        mock_session.request.assert_called_with(
            method="POST",
            url="https://api.example.com/test",
            headers=expected_headers,
            params=None,
            json=data,
            data=None,
            timeout=30
        )

    def test_put_method(self, api_client, mock_session):
        """Test PUT request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"header": {HEADER_SUCCESS_KEY: True}}
        mock_session.request.return_value = mock_response
        
        result = api_client.put("/test/123", json_data={"status": "active"})
        
        assert mock_session.request.called

    def test_delete_method(self, api_client, mock_session):
        """Test DELETE request."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.json.return_value = {"header": {HEADER_SUCCESS_KEY: True}}
        mock_session.request.return_value = mock_response
        
        result = api_client.delete("/test/123")
        
        assert mock_session.request.called

    def test_wait_for_completion_success(self, api_client, mock_session):
        """Test waiting for async operation completion."""
        # Simulate progress updates
        responses = [
            {"list": [{"batchJobCode": "TEST_JOB", "completed": 50, "total": 100}]},
            {"list": [{"batchJobCode": "TEST_JOB", "completed": 100, "total": 100}]}
        ]
        
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"header": {HEADER_SUCCESS_KEY: True}, **responses[0]}
        
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"header": {HEADER_SUCCESS_KEY: True}, **responses[1]}
        
        api_client.get = Mock(side_effect=[responses[0], responses[1]])
        
        result = api_client.wait_for_completion(
            "/check",
            "completed",
            "total",
            "TEST_JOB",
            check_interval=0.1,
            max_wait_time=5
        )
        
        assert result is True
        assert api_client.get.call_count == 2

    def test_wait_for_completion_timeout(self, api_client):
        """Test wait for completion timeout."""
        api_client.get = Mock(return_value={
            "list": [{"batchJobCode": "TEST_JOB", "completed": 50, "total": 100}]
        })
        
        result = api_client.wait_for_completion(
            "/check",
            "completed",
            "total",
            "TEST_JOB",
            check_interval=0.1,
            max_wait_time=0.2
        )
        
        assert result is False

    def test_wait_for_completion_with_error(self, api_client):
        """Test wait for completion with API errors."""
        api_client.get = Mock(side_effect=APIRequestException("Check failed"))
        
        result = api_client.wait_for_completion(
            "/check",
            "completed",
            "total",
            "TEST_JOB",
            check_interval=0.1,
            max_wait_time=0.5
        )
        
        assert result is False

    def test_connection_error_handling(self, api_client, mock_session):
        """Test connection error handling."""
        mock_session.request.side_effect = ConnectionError("Network unreachable")
        
        # ConnectionError is wrapped in APIRequestException
        with pytest.raises(APIRequestException) as exc_info:
            api_client.request("GET", "/test")
        
        assert "Request failed: Network unreachable" in str(exc_info.value)

    def test_timeout_handling(self, api_client, mock_session):
        """Test timeout handling."""
        mock_session.request.side_effect = Timeout("Request timeout")
        
        # Timeout is wrapped in APIRequestException
        with pytest.raises(APIRequestException) as exc_info:
            api_client.request("GET", "/test")
        
        assert "Request failed: Request timeout" in str(exc_info.value)

    @patch('libs.http_client.logger')
    def test_logging(self, mock_logger, api_client):
        """Test logging in various scenarios."""
        api_client.get = Mock(side_effect=APIRequestException("Test error"))
        
        api_client.wait_for_completion(
            "/check", "completed", "total", "TEST_JOB",
            check_interval=0.1, max_wait_time=0.2
        )
        
        mock_logger.warning.assert_called()


class TestSendDataSession:
    """Test legacy SendDataSession wrapper."""

    def test_legacy_wrapper_initialization(self):
        """Test SendDataSession initialization."""
        session = SendDataSession("GET", "https://api.example.com/test")
        assert hasattr(session, 'method')
        assert hasattr(session, 'url')
        assert session.method == "GET"
        assert session.url == "https://api.example.com/test"

    def test_legacy_wrapper_properties(self):
        """Test legacy wrapper properties."""
        session = SendDataSession("POST", "https://api.example.com/test")
        
        # Test property setters
        session.data = "test data"
        session.json = {"key": "value"}
        session.headers = {"X-Test": "test"}
        
        # Test property getters
        assert session.data == "test data"
        assert session.json == {"key": "value"}
        assert session.headers == {"X-Test": "test"}
