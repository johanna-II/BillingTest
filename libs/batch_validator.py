"""Batch Validator for billing batch job validation."""

import re
from datetime import datetime
from typing import List

from .constants import BatchJobCode
from .exceptions import ValidationException


class BatchValidator:
    """Handles batch job validations.

    This class encapsulates pure validation logic for batch jobs,
    making it easier to test independently from API interactions.
    """

    # Valid execution day range
    MIN_EXECUTION_DAY = 1
    MAX_EXECUTION_DAY = 31

    # Month format pattern
    MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")

    # Common batch job combinations
    BILLING_JOB_SEQUENCE = [
        BatchJobCode.API_CALCULATE_USAGE_AND_PRICE,  # Calculate billing
        BatchJobCode.BATCH_GENERATE_STATEMENT,  # Generate statements
        BatchJobCode.BATCH_SEND_INVOICE,  # Send invoices
    ]

    PAYMENT_JOB_SEQUENCE = [
        BatchJobCode.BATCH_PROCESS_PAYMENT,  # Process payments
        BatchJobCode.BATCH_PAYMENT_REMINDER,  # Send reminders
    ]

    @classmethod
    def validate_month_format(cls, month: str) -> None:
        """Validate month format is YYYY-MM.

        Args:
            month: Month string to validate

        Raises:
            ValidationException: If month format is invalid
        """
        # Check regex pattern
        if not cls.MONTH_PATTERN.match(month):
            raise ValidationException(f"Invalid month format: {month}. Expected YYYY-MM")

        # Validate it's a real date
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise ValidationException(f"Invalid month value: {month}. Must be a valid year-month")

    @classmethod
    def validate_job_code(cls, job_code: str) -> None:
        """Validate batch job code.

        Args:
            job_code: Job code to validate

        Raises:
            ValidationException: If job code is invalid
        """
        valid_codes = [code.value for code in BatchJobCode]
        if job_code not in valid_codes:
            raise ValidationException(
                f"Invalid batch job code: {job_code}. " f"Valid codes are: {', '.join(valid_codes)}"
            )

    @classmethod
    def validate_execution_day(cls, execution_day: int) -> None:
        """Validate execution day.

        Args:
            execution_day: Day of month for execution

        Raises:
            ValidationException: If execution day is invalid
        """
        if not cls.MIN_EXECUTION_DAY <= execution_day <= cls.MAX_EXECUTION_DAY:
            raise ValidationException(
                f"Execution day must be between {cls.MIN_EXECUTION_DAY} "
                f"and {cls.MAX_EXECUTION_DAY}: {execution_day}"
            )

    @classmethod
    def is_valid_job_sequence(cls, job_codes: List[str]) -> bool:
        """Check if job codes form a valid sequence.

        Args:
            job_codes: List of job codes to check

        Returns:
            True if sequence is valid
        """
        # Check billing sequence
        if all(code in [job.value for job in cls.BILLING_JOB_SEQUENCE] for code in job_codes):
            return True

        # Check payment sequence
        if all(code in [job.value for job in cls.PAYMENT_JOB_SEQUENCE] for code in job_codes):
            return True

        return False

    @classmethod
    def get_job_category(cls, job_code: str) -> str:
        """Get category of batch job.

        Args:
            job_code: Job code to categorize

        Returns:
            Job category (billing, payment, etc.)
        """
        if "CALCULATE" in job_code or "STATEMENT" in job_code or "INVOICE" in job_code:
            return "billing"
        elif "PAYMENT" in job_code:
            return "payment"
        elif "CREDIT" in job_code:
            return "credit"
        elif "CONTRACT" in job_code:
            return "contract"
        elif "RECONCILIATION" in job_code:
            return "reconciliation"
        else:
            return "other"

    @classmethod
    def get_job_type(cls, job_code: str) -> str:
        """Get type of batch job.

        Args:
            job_code: Job code to type

        Returns:
            Job type (api, batch, etc.)
        """
        if job_code.startswith("API_"):
            return "api"
        elif job_code.startswith("BATCH_"):
            return "batch"
        else:
            return "other"

    @classmethod
    def validate_job_dependencies(cls, job_code: str, completed_jobs: List[str]) -> None:
        """Validate if job dependencies are met.

        Args:
            job_code: Job code to run
            completed_jobs: List of already completed job codes

        Raises:
            ValidationException: If dependencies are not met
        """
        # Define dependencies
        dependencies = {
            BatchJobCode.BATCH_GENERATE_STATEMENT.value: [
                BatchJobCode.API_CALCULATE_USAGE_AND_PRICE.value
            ],
            BatchJobCode.BATCH_SEND_INVOICE.value: [
                BatchJobCode.API_CALCULATE_USAGE_AND_PRICE.value,
                BatchJobCode.BATCH_GENERATE_STATEMENT.value,
            ],
            BatchJobCode.BATCH_PAYMENT_REMINDER.value: [BatchJobCode.BATCH_SEND_INVOICE.value],
        }

        required_jobs = dependencies.get(job_code, [])
        missing_jobs = [job for job in required_jobs if job not in completed_jobs]

        if missing_jobs:
            raise ValidationException(
                f"Job {job_code} requires these jobs to be completed first: "
                f"{', '.join(missing_jobs)}"
            )

    @classmethod
    def calculate_next_execution_date(cls, month: str, execution_day: int) -> datetime:
        """Calculate next execution date for batch job.

        Args:
            month: Target month (YYYY-MM)
            execution_day: Day of month for execution

        Returns:
            Next execution datetime
        """
        year_str, month_str = month.split("-")
        year = int(year_str)
        month_num = int(month_str)

        # Handle edge case where execution_day might not exist in the month
        try:
            execution_date = datetime(year, month_num, execution_day)
        except ValueError:
            # If day doesn't exist (e.g., Feb 31), use last day of month
            if month_num == 12:
                # Next month is January of next year
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month_num + 1, 1)
            # Get last day of current month
            from datetime import timedelta

            execution_date = next_month - timedelta(days=1)

        return execution_date

    @classmethod
    def is_job_idempotent(cls, job_code: str) -> bool:
        """Check if a batch job is idempotent (safe to rerun).

        Args:
            job_code: Job code to check

        Returns:
            True if job is idempotent
        """
        # Read-only and reconciliation jobs are typically idempotent
        idempotent_jobs = [
            BatchJobCode.BATCH_RECONCILIATION.value,
            BatchJobCode.BATCH_PAYMENT_REMINDER.value,  # Just sends reminders
        ]

        return job_code in idempotent_jobs
