"""Unit tests for BatchManager validation logic."""

from unittest.mock import Mock

import pytest

from libs.Batch import BatchManager
from libs.constants import BatchJobCode
from libs.exceptions import ValidationException


class TestBatchValidation:
    """Unit tests for batch job validation logic."""

    @pytest.fixture
    def batch_manager(self):
        """Create BatchManager with mocked client."""
        mock_client = Mock()
        return BatchManager(month="2024-01", client=mock_client)

    def test_validate_month_format_valid(self):
        """Test valid month formats."""
        # Should not raise
        from libs.batch_validator import BatchValidator

        BatchValidator.validate_month_format("2024-01")
        BatchValidator.validate_month_format("2024-12")
        BatchValidator.validate_month_format("2025-06")

    def test_validate_month_format_invalid(self):
        """Test invalid month formats."""
        from libs.batch_validator import BatchValidator

        invalid_formats = [
            "2024",  # Missing month
            "01-2024",  # Wrong order
            "2024-1",  # Single digit month
            "2024-13",  # Invalid month
            "2024-00",  # Zero month
            "24-01",  # 2-digit year
            "2024/01",  # Wrong separator
            "",  # Empty
        ]

        for invalid in invalid_formats:
            with pytest.raises(ValidationException, match="Invalid month"):
                BatchValidator.validate_month_format(invalid)

    def test_job_code_validation_valid(self, batch_manager):
        """Test valid job code validation."""
        batch_manager._client.post.return_value = {"jobId": "123"}

        # Test with enum
        result = batch_manager.request_batch_job(
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE
        )
        assert result["jobId"] == "123"

        # Test with string
        result = batch_manager.request_batch_job("BATCH_GENERATE_STATEMENT")
        assert result["jobId"] == "123"

    def test_job_code_validation_invalid(self, batch_manager):
        """Test invalid job code validation."""
        with pytest.raises(ValidationException, match="Invalid batch job code"):
            batch_manager.request_batch_job("INVALID_JOB_CODE")

    def test_execution_day_validation_valid(self, batch_manager):
        """Test valid execution day range."""
        batch_manager._client.post.return_value = {"success": True}

        # Test boundary values
        for day in [1, 15, 28, 31]:
            result = batch_manager.request_batch_job(
                BatchJobCode.API_CALCULATE_USAGE_AND_PRICE, execution_day=day
            )
            assert result["success"] is True

    def test_execution_day_validation_invalid(self, batch_manager):
        """Test invalid execution day values."""
        # Test below minimum
        with pytest.raises(ValidationException, match="Execution day must be between"):
            batch_manager.request_batch_job(
                BatchJobCode.API_CALCULATE_USAGE_AND_PRICE, execution_day=0
            )

        # Test above maximum
        with pytest.raises(ValidationException, match="Execution day must be between"):
            batch_manager.request_batch_job(
                BatchJobCode.API_CALCULATE_USAGE_AND_PRICE, execution_day=32
            )

        # Test negative
        with pytest.raises(ValidationException, match="Execution day must be between"):
            batch_manager.request_batch_job(
                BatchJobCode.API_CALCULATE_USAGE_AND_PRICE, execution_day=-1
            )

    def test_batch_request_data_structure(self, batch_manager):
        """Test batch request data structure."""
        batch_manager._client.post.return_value = {"success": True}

        batch_manager.request_batch_job(
            job_code=BatchJobCode.API_CALCULATE_USAGE_AND_PRICE,
            async_mode=True,
            execution_day=15,
            locale="ko_KR",
        )

        # Check the posted data
        call_args = batch_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]

        assert posted_data["date"] == "2024-01-15T00:00:00+09:00"
        assert posted_data["batchJobCode"] == "API_CALCULATE_USAGE_AND_PRICE"
        assert posted_data["is_async"] == "true"

        # Check headers
        headers = call_args[1]["headers"]
        assert headers["lang"] == "ko"

    def test_date_formatting(self, batch_manager):
        """Test date formatting with different execution days."""
        batch_manager._client.post.return_value = {"success": True}

        # Test single digit day
        batch_manager.request_batch_job(
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE, execution_day=5
        )
        call_args = batch_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]
        assert (
            posted_data["date"] == "2024-01-05T00:00:00+09:00"
        )  # Should be zero-padded

        # Test double digit day
        batch_manager.request_batch_job(
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE, execution_day=25
        )
        call_args = batch_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]
        assert posted_data["date"] == "2024-01-25T00:00:00+09:00"

    def test_all_batch_job_codes(self, batch_manager):
        """Test all valid batch job codes."""
        batch_manager._client.post.return_value = {"success": True}

        # Test all enum values
        for job_code in BatchJobCode:
            result = batch_manager.request_batch_job(job_code)
            assert result["success"] is True

    def test_async_mode_handling(self, batch_manager):
        """Test async mode parameter handling."""
        batch_manager._client.post.return_value = {"success": True}

        # Test async=True
        batch_manager.request_batch_job(
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE, async_mode=True
        )
        call_args = batch_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]
        assert posted_data["is_async"] == "true"

        # Test async=False
        batch_manager.request_batch_job(
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE, async_mode=False
        )
        call_args = batch_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]
        assert posted_data["is_async"] == "false"
