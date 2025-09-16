"""Batch job management for billing system."""

from __future__ import annotations

import contextlib
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from config import url

from .constants import DEFAULT_LOCALE, BatchJobCode
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient

if TYPE_CHECKING:
    from .types import BatchRequestData

logger = logging.getLogger(__name__)


class BatchManager:
    """Manages batch job operations for billing system."""

    def __init__(self, month: str) -> None:
        """Initialize batch manager.

        Args:
            month: Target month in YYYY-MM format

        Raises:
            ValidationException: If month format is invalid
        """
        self._validate_month_format(month)
        self.month = month
        self._client = BillingAPIClient(url.BASE_BILLING_URL)

    def __repr__(self) -> str:
        return f"BatchManager(month={self.month})"

    @staticmethod
    def _validate_month_format(month: str) -> None:
        """Validate month format is YYYY-MM."""
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            msg = f"Invalid month format: {month}. Expected YYYY-MM"
            raise ValidationException(
                msg
            )

    def request_batch_job(
        self,
        job_code: BatchJobCode | str,
        async_mode: bool = True,
        execution_day: int = 15,
        locale: str = DEFAULT_LOCALE,
    ) -> dict[str, Any]:
        """Request execution of a batch job.

        Args:
            job_code: Batch job code to execute
            async_mode: Whether to run asynchronously
            execution_day: Day of month for execution (1-31)
            locale: Locale for the batch job

        Returns:
            API response data

        Raises:
            ValidationException: If parameters are invalid
            APIRequestException: If batch request fails
        """
        # Normalize job code
        job_code_str = (
            job_code.value if isinstance(job_code, BatchJobCode) else job_code
        )

        # Validate job code
        valid_codes = [code.value for code in BatchJobCode]
        if job_code_str not in valid_codes:
            msg = (
                f"Invalid batch job code: {job_code_str}. "
                f"Valid codes are: {', '.join(valid_codes)}"
            )
            raise ValidationException(
                msg
            )

        # Validate execution day
        if not 1 <= execution_day <= 31:
            msg = f"Execution day must be between 1 and 31: {execution_day}"
            raise ValidationException(
                msg
            )

        # Build execution timestamp
        execution_date = f"{self.month}-{execution_day:02d}T00:00:00+09:00"

        # Build request data
        batch_data: BatchRequestData = {
            "is_async": "true" if async_mode else "false",
            "batchJobCode": job_code_str,
            "date": execution_date,
        }

        headers = {
            "Accept": "application/json",
            "lang": locale.split("_")[0] if "_" in locale else locale,
        }

        endpoint = "billing/admin/batches"

        logger.info("Requesting batch job {job_code_str} for %s", self.month)

        try:
            response = self._client.post(
                endpoint, headers=headers, json_data=batch_data
            )
            logger.info("Successfully requested batch job %s", job_code_str)
            return response
        except APIRequestException as e:
            logger.exception("Failed to request batch job: %s", e)
            raise

    def get_batch_status(self, job_code: BatchJobCode | str) -> dict[str, Any]:
        """Get status of a batch job.

        Args:
            job_code: Batch job code to check

        Returns:
            Batch job status information

        Raises:
            APIRequestException: If status check fails
        """
        # This would typically query a batch status endpoint
        # For now, returning placeholder as the original code doesn't have this
        logger.info("Checking status for batch job %s", job_code)

        # Note: Implementation would depend on actual API endpoints
        # This is a placeholder for future enhancement
        return {
            "job_code": job_code,
            "status": "UNKNOWN",
            "message": "Status check not implemented in original code",
        }

    def request_common_batch_jobs(self) -> dict[str, Any]:
        """Request common batch jobs for the month.

        Returns:
            Dictionary with results for each batch job
        """
        common_jobs = [
            BatchJobCode.BATCH_GENERATE_STATEMENT,
            BatchJobCode.API_CALCULATE_USAGE_AND_PRICE,
            BatchJobCode.BATCH_CREDIT_EXPIRY,
        ]

        results = {}

        for job_code in common_jobs:
            try:
                result = self.request_batch_job(job_code)
                results[job_code.value] = {"success": True, "response": result}
            except APIRequestException as e:
                results[job_code.value] = {"success": False, "error": str(e)}
                logger.exception("Failed to request {job_code.value}: %s", e)

        return results


# Backward compatibility wrapper
class Batches:
    """Legacy wrapper for backward compatibility."""

    def __init__(self, month: str) -> None:
        self.month = month
        self._batchJobCode = ""
        self._manager = BatchManager(month)

    def __repr__(self) -> str:
        return f"Batches(month: {self.month}, batchJobCode: {self.batchJobCode})"

    @property
    def batch_job_code(self):
        return self._batchJobCode

    @batchJobCode.setter
    def batch_job_code(self, batchJobCode) -> None:
        self._batchJobCode = batchJobCode

    def send_batch_request(self) -> None:
        """Legacy method for sending batch request."""
        with contextlib.suppress(Exception):
            self._manager.request_batch_job(self.batchJobCode)
