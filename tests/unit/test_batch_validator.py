"""Unit tests for BatchValidator - pure batch job validation logic."""

from datetime import datetime

import pytest

from libs.batch_validator import BatchValidator
from libs.constants import BatchJobCode
from libs.exceptions import ValidationException


class TestBatchValidator:
    """Unit tests for batch job validation logic."""

    def test_validate_month_format_valid(self):
        """Test valid month formats."""
        # Should not raise
        BatchValidator.validate_month_format("2024-01")
        BatchValidator.validate_month_format("2024-12")
        BatchValidator.validate_month_format("2025-06")

    def test_validate_month_format_invalid(self):
        """Test invalid month formats."""
        invalid_formats = [
            "2024",  # Missing month
            "01-2024",  # Wrong order
            "2024-1",  # Single digit month
            "2024-13",  # Invalid month
            "2024-00",  # Zero month
            "24-01",  # 2-digit year
            "2024/01",  # Wrong separator
            "",  # Empty
            "abc",  # Non-numeric
        ]

        for invalid in invalid_formats:
            with pytest.raises(ValidationException, match="Invalid month"):
                BatchValidator.validate_month_format(invalid)

    def test_validate_job_code_valid(self):
        """Test valid job codes."""
        # Should not raise
        for job_code in BatchJobCode:
            BatchValidator.validate_job_code(job_code.value)

    def test_validate_job_code_invalid(self):
        """Test invalid job codes."""
        with pytest.raises(ValidationException, match="Invalid batch job code"):
            BatchValidator.validate_job_code("INVALID_JOB")

        with pytest.raises(ValidationException, match="Invalid batch job code"):
            BatchValidator.validate_job_code("")

    def test_validate_execution_day_valid(self):
        """Test valid execution days."""
        # Should not raise
        BatchValidator.validate_execution_day(1)
        BatchValidator.validate_execution_day(15)
        BatchValidator.validate_execution_day(31)

    def test_validate_execution_day_invalid(self):
        """Test invalid execution days."""
        invalid_days = [0, -1, 32, 100]

        for day in invalid_days:
            with pytest.raises(
                ValidationException, match="Execution day must be between"
            ):
                BatchValidator.validate_execution_day(day)

    def test_is_valid_job_sequence(self):
        """Test job sequence validation."""
        # Valid billing sequence
        billing_jobs = [
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE.value,
            BatchJobCode.BATCH_GENERATE_STATEMENT.value,
        ]
        assert BatchValidator.is_valid_job_sequence(billing_jobs)

        # Valid payment sequence
        payment_jobs = [
            BatchJobCode.BATCH_PROCESS_PAYMENT.value,
            BatchJobCode.BATCH_PAYMENT_REMINDER.value,
        ]
        assert BatchValidator.is_valid_job_sequence(payment_jobs)

        # Mixed sequence (invalid)
        mixed_jobs = [
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE.value,
            BatchJobCode.BATCH_PROCESS_PAYMENT.value,
        ]
        assert not BatchValidator.is_valid_job_sequence(mixed_jobs)

    def test_get_job_category(self):
        """Test job category detection."""
        assert (
            BatchValidator.get_job_category("API_CALCULATE_USAGE_AND_PRICE")
            == "billing"
        )
        assert BatchValidator.get_job_category("BATCH_GENERATE_STATEMENT") == "billing"
        assert BatchValidator.get_job_category("BATCH_PROCESS_PAYMENT") == "payment"
        assert BatchValidator.get_job_category("BATCH_CREDIT_EXPIRY") == "credit"
        assert BatchValidator.get_job_category("BATCH_CONTRACT_RENEWAL") == "contract"
        assert (
            BatchValidator.get_job_category("BATCH_RECONCILIATION") == "reconciliation"
        )
        assert BatchValidator.get_job_category("UNKNOWN_JOB") == "other"

    def test_get_job_type(self):
        """Test job type detection."""
        assert BatchValidator.get_job_type("API_CALCULATE_USAGE_AND_PRICE") == "api"
        assert BatchValidator.get_job_type("BATCH_GENERATE_STATEMENT") == "batch"
        assert BatchValidator.get_job_type("BATCH_PROCESS_PAYMENT") == "batch"
        assert BatchValidator.get_job_type("CUSTOM_JOB") == "other"

    def test_validate_job_dependencies_success(self):
        """Test job dependency validation when dependencies are met."""
        # Statement generation with calculation completed
        completed = [BatchJobCode.API_CALCULATE_USAGE_AND_PRICE.value]
        BatchValidator.validate_job_dependencies(
            BatchJobCode.BATCH_GENERATE_STATEMENT.value, completed
        )

        # Invoice sending with all dependencies completed
        completed = [
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE.value,
            BatchJobCode.BATCH_GENERATE_STATEMENT.value,
        ]
        BatchValidator.validate_job_dependencies(
            BatchJobCode.BATCH_SEND_INVOICE.value, completed
        )

    def test_validate_job_dependencies_failure(self):
        """Test job dependency validation when dependencies are not met."""
        # Statement generation without calculation
        with pytest.raises(ValidationException, match="requires these jobs"):
            BatchValidator.validate_job_dependencies(
                BatchJobCode.BATCH_GENERATE_STATEMENT.value, []
            )

        # Invoice sending without prerequisites
        with pytest.raises(ValidationException, match="requires these jobs"):
            BatchValidator.validate_job_dependencies(
                BatchJobCode.BATCH_SEND_INVOICE.value, []
            )

    def test_calculate_next_execution_date(self):
        """Test next execution date calculation."""
        # Normal case
        exec_date = BatchValidator.calculate_next_execution_date("2024-01", 15)
        assert exec_date == datetime(2024, 1, 15)

        # End of month
        exec_date = BatchValidator.calculate_next_execution_date("2024-02", 28)
        assert exec_date == datetime(2024, 2, 28)

        # Day doesn't exist (Feb 31) - should use last day
        exec_date = BatchValidator.calculate_next_execution_date("2024-02", 31)
        assert exec_date == datetime(2024, 2, 29)  # 2024 is leap year

        # December edge case
        exec_date = BatchValidator.calculate_next_execution_date("2024-12", 31)
        assert exec_date == datetime(2024, 12, 31)

    def test_is_job_idempotent(self):
        """Test idempotent job detection."""
        # Idempotent jobs
        assert BatchValidator.is_job_idempotent(BatchJobCode.BATCH_RECONCILIATION.value)
        assert BatchValidator.is_job_idempotent(
            BatchJobCode.BATCH_PAYMENT_REMINDER.value
        )

        # Non-idempotent jobs
        assert not BatchValidator.is_job_idempotent(
            BatchJobCode.BATCH_PROCESS_PAYMENT.value
        )
        assert not BatchValidator.is_job_idempotent(
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE.value
        )
        assert not BatchValidator.is_job_idempotent(
            BatchJobCode.BATCH_CREDIT_EXPIRY.value
        )
