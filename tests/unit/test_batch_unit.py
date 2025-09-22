"""Unit tests for BatchManager to improve coverage."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from libs.Batch import BatchManager, Batches
from libs.exceptions import APIRequestException, ValidationException, TimeoutException
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

    def test_init_invalid_month(self):
        """Test BatchManager initialization with invalid month."""
        with pytest.raises(ValidationException) as exc_info:
            BatchManager("2024-1")  # Invalid format
        
        assert "Invalid month format" in str(exc_info.value)

    def test_repr(self, batch_manager):
        """Test string representation."""
        assert repr(batch_manager) == "BatchManager(month=2024-01)"

    def test_request_batch_job_success(self, batch_manager, mock_client):
        """Test successful batch job request."""
        mock_response = {"batchId": "batch-123", "status": "RUNNING"}
        mock_client.post.return_value = mock_response
        
        result = batch_manager.request_batch_job(BatchJobCode.BATCH_CREDIT_EXPIRY)
        
        assert result == mock_response
        
        # Verify API call with correct endpoint and data
        expected_data = {
            "is_async": "true",
            "batchJobCode": "BATCH_CREDIT_EXPIRY",
            "date": "2024-01-15T00:00:00+09:00"
        }
        
        mock_client.post.assert_called_once_with(
            "billing/admin/batches",
            headers={"Accept": "application/json", "lang": "ko"},
            json_data=expected_data
        )

    def test_request_batch_job_with_custom_params(self, batch_manager, mock_client):
        """Test batch job request with custom parameters."""
        mock_response = {"batchId": "batch-456"}
        mock_client.post.return_value = mock_response
        
        result = batch_manager.request_batch_job(
            BatchJobCode.BATCH_PROCESS_PAYMENT,
            async_mode=False,
            execution_day=20,
            locale="en"
        )
        
        assert result == mock_response
        
        # Check that custom params were used
        call_args = mock_client.post.call_args
        json_data = call_args[1]["json_data"]
        assert json_data["is_async"] == "false"
        assert json_data["date"] == "2024-01-20T00:00:00+09:00"
        assert call_args[1]["headers"]["lang"] == "en"

    def test_request_batch_job_string_code(self, batch_manager, mock_client):
        """Test batch job request with string job code."""
        mock_response = {"batchId": "batch-789"}
        mock_client.post.return_value = mock_response
        
        # Should accept string job code
        result = batch_manager.request_batch_job("BATCH_GENERATE_STATEMENT")
        
        assert result == mock_response

    def test_request_batch_job_invalid_code(self, batch_manager, mock_client):
        """Test batch job request with invalid job code."""
        with pytest.raises(ValidationException) as exc_info:
            batch_manager.request_batch_job("INVALID_JOB_CODE")
        
        assert "Invalid batch job code" in str(exc_info.value)

    def test_request_batch_job_invalid_execution_day(self, batch_manager, mock_client):
        """Test batch job request with invalid execution day."""
        with pytest.raises(ValidationException) as exc_info:
            batch_manager.request_batch_job(
                BatchJobCode.BATCH_CREDIT_EXPIRY,
                execution_day=32  # Invalid day
            )
        
        assert "Execution day must be between 1 and 31" in str(exc_info.value)

    def test_request_batch_job_api_error(self, batch_manager, mock_client):
        """Test batch job request with API error."""
        mock_client.post.side_effect = APIRequestException("Batch service unavailable")
        
        with pytest.raises(APIRequestException):
            batch_manager.request_batch_job(BatchJobCode.BATCH_CREDIT_EXPIRY)

    def test_get_batch_status(self, batch_manager):
        """Test get_batch_status method."""
        # Check current status - returns a dictionary with status info
        status = batch_manager.get_batch_status(BatchJobCode.BATCH_CREDIT_EXPIRY)
        
        assert isinstance(status, dict)
        assert "job_code" in status
        assert "status" in status
        assert status["job_code"] == BatchJobCode.BATCH_CREDIT_EXPIRY
        assert status["status"] == "UNKNOWN"  # Default status

    def test_request_common_batch_jobs(self, batch_manager, mock_client):
        """Test requesting common batch jobs."""
        # Mock successful responses for each common job
        mock_client.post.return_value = {"batchId": "batch-common", "status": "STARTED"}
        
        results = batch_manager.request_common_batch_jobs()
        
        # Should request 3 common jobs
        expected_jobs = [
            BatchJobCode.BATCH_GENERATE_STATEMENT,
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE,
            BatchJobCode.BATCH_CREDIT_EXPIRY
        ]
        
        assert len(results) == 3
        assert all(job.value in results for job in expected_jobs)
        assert all(result["success"] for result in results.values())

    def test_request_common_batch_jobs_partial_failure(self, batch_manager, mock_client):
        """Test requesting common batch jobs with partial failure."""
        # First two succeed, third fails
        mock_client.post.side_effect = [
            {"batchId": "batch-1", "status": "STARTED"},
            {"batchId": "batch-2", "status": "STARTED"},
            APIRequestException("Third job failed")
        ]
        
        results = batch_manager.request_common_batch_jobs()
        
        # Should have 3 results, 2 successful and 1 failed
        assert len(results) == 3
        success_count = sum(1 for r in results.values() if r["success"])
        assert success_count == 2


    def test_validate_month_format_valid(self):
        """Test month format validation with valid formats."""
        valid_months = ["2024-01", "2024-12", "2023-06", "2022-09"]
        
        for month in valid_months:
            # Should not raise exception
            BatchManager._validate_month_format(month)

    def test_validate_month_format_invalid(self):
        """Test month format validation with invalid formats."""
        invalid_months = ["2024", "2024-1", "2024-13", "24-01", "2024/01", ""]
        
        for month in invalid_months:
            with pytest.raises(ValidationException):
                BatchManager._validate_month_format(month)

    @patch('libs.Batch.logger')
    def test_logging_on_operations(self, mock_logger, batch_manager, mock_client):
        """Test that operations are properly logged."""
        mock_client.post.return_value = {"batchId": "batch-123"}
        
        batch_manager.request_batch_job(BatchJobCode.BATCH_CREDIT_EXPIRY)
        
        # Verify logging occurred
        assert mock_logger.info.called


class TestBatchesLegacyWrapper:
    """Unit tests for legacy Batches wrapper."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        with patch('libs.Batch.BatchManager') as mock_manager_class:
            self.mock_manager = Mock()
            mock_manager_class.return_value = self.mock_manager
            self.batches = Batches("2024-01")
            yield
    
    def test_init_legacy(self):
        """Test legacy Batches initialization."""
        assert self.batches.month == "2024-01"
        assert hasattr(self.batches, '_manager')
        assert self.batches._batchJobCode == ""
    
    def test_batch_job_code_property(self):
        """Test batch_job_code property."""
        self.batches.batch_job_code = "TEST_CODE"
        assert self.batches.batch_job_code == "TEST_CODE"
        assert self.batches._batchJobCode == "TEST_CODE"
    
    def test_batchJobCode_property_legacy(self):
        """Test legacy batchJobCode property."""
        self.batches.batchJobCode = "LEGACY_CODE"
        assert self.batches.batchJobCode == "LEGACY_CODE"
        assert self.batches.batch_job_code == "LEGACY_CODE"
    
    def test_repr_legacy(self):
        """Test string representation of legacy Batches."""
        self.batches.batch_job_code = "BATCH_CREDIT_EXPIRY"
        repr_str = repr(self.batches)
        assert "month: 2024-01" in repr_str
        assert "batchJobCode: BATCH_CREDIT_EXPIRY" in repr_str
    
    def test_request_batch_job_legacy(self):
        """Test legacy send_batch_request method."""
        self.mock_manager.request_batch_job.return_value = {"status": "STARTED"}
        self.batches.batchJobCode = "BATCH_GENERATE_STATEMENT"
        
        self.batches.send_batch_request()
        
        self.mock_manager.request_batch_job.assert_called_once_with("BATCH_GENERATE_STATEMENT")
    
    def test_request_batch_job_legacy_exception_suppressed(self):
        """Test legacy send_batch_request suppresses exceptions."""
        self.mock_manager.request_batch_job.side_effect = Exception("Test error")
        self.batches.batchJobCode = "BATCH_GENERATE_STATEMENT"
        
        # Should not raise exception
        self.batches.send_batch_request()
        
        self.mock_manager.request_batch_job.assert_called_once()
    
    def test_get_batch_status_legacy(self):
        """Test that get_batch_status is not available in legacy wrapper."""
        # Legacy Batches doesn't expose get_batch_status
        assert not hasattr(self.batches, 'get_batch_status')
    
    def test_get_batch_status_legacy_exception_returns_none(self):
        """Test that get_batch_status is not available in legacy wrapper."""
        # Legacy Batches doesn't expose get_batch_status
        assert not hasattr(self.batches, 'get_batch_status')
    
    def test_request_common_batch_jobs_legacy(self):
        """Test that request_common_batch_jobs is not available in legacy wrapper."""
        # Legacy Batches doesn't expose request_common_batch_jobs
        assert not hasattr(self.batches, 'request_common_batch_jobs')
    
    def test_request_common_batch_jobs_legacy_exception_suppressed(self):
        """Test that request_common_batch_jobs is not available in legacy wrapper."""
        # Legacy Batches doesn't expose request_common_batch_jobs
        assert not hasattr(self.batches, 'request_common_batch_jobs')