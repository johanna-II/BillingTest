"""Unit tests for BatchManager to improve coverage."""

from unittest.mock import Mock, patch

import pytest

from libs.Batch import BatchManager
from libs.constants import BatchJobCode
from libs.exceptions import APIRequestException, ValidationException


class TestBatchManagerUnit:
    """Unit tests for BatchManager class."""

    @pytest.fixture
    def mock_client(self):
        """Mock HTTP client."""
        return Mock()

    @pytest.fixture
    def batch_manager(self, mock_client):
        """Create BatchManager with mocked dependencies."""
        with patch("libs.Batch.BillingAPIClient", return_value=mock_client):
            manager = BatchManager("2024-01")
            manager._client = mock_client
            return manager

    def test_request_batch_job_success(self, batch_manager, mock_client) -> None:
        """Test successful batch job request."""
        mock_response = {"batchId": "batch-123", "status": "RUNNING"}
        mock_client.post.return_value = mock_response

        result = batch_manager.request_batch_job(BatchJobCode.BATCH_CREDIT_EXPIRY)

        assert result == mock_response

        # Verify API call with correct endpoint and data
        expected_data = {
            "is_async": "true",
            "batchJobCode": "BATCH_CREDIT_EXPIRY",
            "date": "2024-01-15T00:00:00+09:00",
        }

        mock_client.post.assert_called_once_with(
            "billing/admin/batches",
            headers={"Accept": "application/json", "lang": "ko"},
            json_data=expected_data,
        )

    def test_request_batch_job_with_custom_params(
        self, batch_manager, mock_client
    ) -> None:
        """Test batch job request with custom parameters."""
        mock_response = {"batchId": "batch-456"}
        mock_client.post.return_value = mock_response

        result = batch_manager.request_batch_job(
            BatchJobCode.BATCH_PROCESS_PAYMENT,
            async_mode=False,
            execution_day=20,
            locale="en",
        )

        assert result == mock_response

        # Check that custom params were used
        call_args = mock_client.post.call_args
        json_data = call_args[1]["json_data"]
        assert json_data["is_async"] == "false"
        assert json_data["date"] == "2024-01-20T00:00:00+09:00"
        assert call_args[1]["headers"]["lang"] == "en"

    def test_request_batch_job_string_code(self, batch_manager, mock_client) -> None:
        """Test batch job request with string job code."""
        mock_response = {"batchId": "batch-789"}
        mock_client.post.return_value = mock_response

        # Should accept string job code
        result = batch_manager.request_batch_job("BATCH_GENERATE_STATEMENT")

        assert result == mock_response

    def test_request_batch_job_invalid_code(self, batch_manager, mock_client) -> None:
        """Test batch job request with invalid job code."""
        with pytest.raises(ValidationException) as exc_info:
            batch_manager.request_batch_job("INVALID_JOB_CODE")

        assert "Invalid batch job code" in str(exc_info.value)

    def test_request_batch_job_invalid_execution_day(
        self, batch_manager, mock_client
    ) -> None:
        """Test batch job request with invalid execution day."""
        with pytest.raises(ValidationException) as exc_info:
            batch_manager.request_batch_job(
                BatchJobCode.BATCH_CREDIT_EXPIRY,
                execution_day=32,  # Invalid day
            )

        assert "Execution day must be between 1 and 31" in str(exc_info.value)

    def test_get_batch_status(self, batch_manager) -> None:
        """Test get_batch_status method."""
        # Check current status - returns a dictionary with status info
        status = batch_manager.get_batch_status(BatchJobCode.BATCH_CREDIT_EXPIRY)

        assert isinstance(status, dict)
        assert "job_code" in status
        assert "status" in status
        assert status["job_code"] == BatchJobCode.BATCH_CREDIT_EXPIRY
        assert status["status"] == "UNKNOWN"  # Default status

    def test_request_common_batch_jobs(self, batch_manager, mock_client) -> None:
        """Test requesting common batch jobs."""
        # Mock successful responses for each common job
        mock_client.post.return_value = {"batchId": "batch-common", "status": "STARTED"}

        results = batch_manager.request_common_batch_jobs()

        # Should request 3 common jobs
        expected_jobs = [
            BatchJobCode.BATCH_GENERATE_STATEMENT,
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE,
            BatchJobCode.BATCH_CREDIT_EXPIRY,
        ]

        assert len(results) == 3
        assert all(job.value in results for job in expected_jobs)
        assert all(result["success"] for result in results.values())

    def test_request_common_batch_jobs_partial_failure(
        self, batch_manager, mock_client
    ) -> None:
        """Test requesting common batch jobs with partial failure."""
        # First two succeed, third fails
        mock_client.post.side_effect = [
            {"batchId": "batch-1", "status": "STARTED"},
            {"batchId": "batch-2", "status": "STARTED"},
            APIRequestException("Third job failed"),
        ]

        results = batch_manager.request_common_batch_jobs()

        # Should have 3 results, 2 successful and 1 failed
        assert len(results) == 3
        success_count = sum(1 for r in results.values() if r["success"])
        assert success_count == 2
