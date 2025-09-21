"""Unit tests for BatchManager to improve coverage."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from libs.Batch import BatchManager, Batches
from libs.exceptions import APIRequestException, TimeoutException
from libs.constants import BatchJobCode


class TestBatchManagerUnit:
    """Unit tests for BatchManager class."""

    @pytest.fixture
    def mock_client(self):
        """Mock HTTP client."""
        return Mock()

    @pytest.fixture
    def batch_manager(self, mock_client):
        """Create BatchManager with mocked dependencies."""
        with patch('libs.Batch.BillingAPIClient', return_value=mock_client):
            manager = BatchManager("2024-01")
            manager._client = mock_client
            return manager

    def test_init(self):
        """Test BatchManager initialization."""
        manager = BatchManager("2024-01")
        assert hasattr(manager, '_client')
        assert manager.month == "2024-01"

    def test_repr(self, batch_manager):
        """Test string representation."""
        assert repr(batch_manager) == "BatchManager(month=2024-01)"

    def test_request_batch_job_success(self, batch_manager, mock_client):
        """Test successful batch job request."""
        mock_response = {"batchId": "batch-123", "status": "RUNNING"}
        mock_client.post.return_value = mock_response
        
        result = batch_manager.request_batch_job(BatchJobCode.BATCH_CREDIT_EXPIRY)
        
        assert result == mock_response
        mock_client.post.assert_called_once_with(
            "batch/jobs",
            json_data={
                "month": "2024-01",
                "jobCode": "BATCH_CREDIT_EXPIRY"
            }
        )

    def test_validate_month_format_invalid(self, batch_manager):
        """Test invalid month format validation."""
        with pytest.raises(ValueError, match="Invalid month format"):
            BatchManager._validate_month_format("2024-1")  # Missing zero padding
        
        with pytest.raises(ValueError, match="Invalid month format"):
            BatchManager._validate_month_format("24-01")  # Wrong year format

    def test_get_batch_status_success(self, batch_manager, mock_client):
        """Test successful batch status retrieval."""
        mock_response = {
            "jobCode": "BATCH_CREDIT_EXPIRY",
            "status": "COMPLETED",
            "completedCount": 100,
            "totalCount": 100
        }
        mock_client.get.return_value = mock_response
        
        status = batch_manager.get_batch_status(BatchJobCode.BATCH_CREDIT_EXPIRY)
        
        assert status == mock_response
        mock_client.get.assert_called_once_with(
            "batch/jobs/status",
            params={"month": "2024-01", "jobCode": "BATCH_CREDIT_EXPIRY"}
        )

    def test_get_batch_status_error(self, batch_manager, mock_client):
        """Test batch status retrieval with error."""
        mock_client.get.side_effect = APIRequestException("Failed to get status")
        
        with pytest.raises(APIRequestException):
            batch_manager.get_batch_status(BatchJobCode.BATCH_CREDIT_EXPIRY)

    def test_request_common_batch_jobs(self, batch_manager, mock_client):
        """Test requesting common batch jobs."""
        mock_responses = [
            {"jobCode": "API_CALCULATE_USAGE_AND_PRICE", "status": "STARTED"},
            {"jobCode": "BATCH_GENERATE_STATEMENT", "status": "STARTED"},
            {"jobCode": "BATCH_PROCESS_PAYMENT", "status": "STARTED"}
        ]
        mock_client.post.side_effect = mock_responses
        
        results = batch_manager.request_common_batch_jobs()
        
        assert "API_CALCULATE_USAGE_AND_PRICE" in results
        assert "BATCH_GENERATE_STATEMENT" in results
        assert "BATCH_PROCESS_PAYMENT" in results
        assert mock_client.post.call_count == 3

    def test_request_batch_job_with_params(self, batch_manager, mock_client):
        """Test batch job request with additional parameters."""
        mock_response = {"batchId": "batch-456"}
        mock_client.post.return_value = mock_response
        
        result = batch_manager.request_batch_job(
            BatchJobCode.BATCH_PROCESS_PAYMENT,
            params={"forceRun": True}
        )
        
        assert result == mock_response
        # Check that params were included in the request
        _, kwargs = mock_client.post.call_args
        assert kwargs["json_data"]["forceRun"] is True

    def test_legacy_batches_class(self):
        """Test legacy Batches class."""
        batch = Batches("2024-01")
        assert batch.month == "2024-01"
        
        # Test batch job code property
        batch.batch_job_code = "TEST_CODE"
        assert batch.batch_job_code == "TEST_CODE"
        assert batch.batchJobCode == "TEST_CODE"  # Legacy property
        
        # Test repr
        assert "month: 2024-01" in repr(batch)
        assert "batchJobCode: TEST_CODE" in repr(batch)

    def test_month_validation_in_constructor(self):
        """Test month validation in constructor."""
        # Valid month should work
        manager = BatchManager("2024-01")
        assert manager.month == "2024-01"
        
        # Invalid month should raise error
        with pytest.raises(ValueError, match="Invalid month format"):
            BatchManager("invalid-month")

    def test_batch_job_code_values(self):
        """Test BatchJobCode enum values."""
        # Test that enum has the expected attributes
        expected_codes = [
            "API_CALCULATE_USAGE_AND_PRICE",
            "BATCH_GENERATE_STATEMENT",
            "BATCH_PROCESS_PAYMENT",
            "BATCH_CREDIT_EXPIRY",
            "BATCH_CONTRACT_RENEWAL"
        ]
        
        for code in expected_codes:
            assert hasattr(BatchJobCode, code)
            # Value should be the same as the name for StrEnum
            assert getattr(BatchJobCode, code).value == code

    @patch('libs.Batch.logger')
    def test_logging_on_operations(self, mock_logger, batch_manager, mock_client):
        """Test that operations are properly logged."""
        mock_client.post.return_value = {"batchId": "batch-123"}
        
        batch_manager.request_batch_job(BatchJobCode.BATCH_CREDIT_EXPIRY)
        
        mock_logger.info.assert_called()

    def test_error_handling_in_batch_request(self, batch_manager, mock_client):
        """Test error handling in batch request."""
        mock_client.post.side_effect = APIRequestException("Batch service unavailable")
        
        with pytest.raises(APIRequestException):
            batch_manager.request_batch_job(BatchJobCode.BATCH_CREDIT_EXPIRY)

    def test_str_enum_usage(self):
        """Test that BatchJobCode StrEnum works correctly."""
        # Test string comparison
        assert BatchJobCode.BATCH_CREDIT_EXPIRY == "BATCH_CREDIT_EXPIRY"
        assert str(BatchJobCode.BATCH_CREDIT_EXPIRY) == "BATCH_CREDIT_EXPIRY"
        
        # Test using string in place of enum
        batch_manager = BatchManager("2024-01")
        mock_client = Mock()
        batch_manager._client = mock_client
        mock_client.post.return_value = {"status": "OK"}
        
        # Should accept both enum and string
        result1 = batch_manager.request_batch_job(BatchJobCode.BATCH_CREDIT_EXPIRY)
        result2 = batch_manager.request_batch_job("BATCH_CREDIT_EXPIRY")
        
        assert result1 == result2
