"""Calculation management for billing system."""

import contextlib
import logging
from typing import Any

from config import url

from .constants import BatchJobCode
from .exceptions import APIRequestException
from .http_client import BillingAPIClient

logger = logging.getLogger(__name__)


class CalculationManager:
    """Manages billing calculations and resource cleanup."""

    def __init__(self, month: str, uuid: str) -> None:
        """Initialize calculation manager.

        Args:
            month: Target month in YYYY-MM format
            uuid: User UUID for calculations
        """
        self.month = month
        self.uuid = uuid
        self._client = BillingAPIClient(url.BASE_BILLING_URL)

    def __repr__(self) -> str:
        return f"CalculationManager(month={self.month}, uuid={self.uuid})"

    def recalculate_all(
        self, include_usage: bool = True, timeout: int = 300
    ) -> dict[str, Any]:
        """Request full recalculation for the month.

        Args:
            include_usage: Whether to include usage recalculation
            timeout: Maximum time to wait for completion in seconds

        Returns:
            API response data

        Raises:
            APIRequestException: If calculation request fails
        """
        endpoint = "billing/admin/calculations"
        data = {"includeUsage": include_usage, "month": self.month, "uuid": self.uuid}

        logger.info("Requesting full recalculation for {self.uuid} in %s", self.month)

        try:
            response = self._client.post(endpoint, json_data=data)
            logger.info("Recalculation request submitted successfully")

            # Wait for calculation to complete
            if self._wait_for_calculation_completion(timeout):
                logger.info("Recalculation completed successfully")
            else:
                logger.warning("Recalculation did not complete within %s seconds", timeout
                )

            return response

        except APIRequestException as e:
            logger.exception("Failed to request recalculation: %s", e)
            raise

    def _wait_for_calculation_completion(
        self, timeout: int = 300, check_interval: int = 3
    ) -> bool:
        """Wait for calculation to complete.

        Args:
            timeout: Maximum time to wait in seconds
            check_interval: Seconds between progress checks

        Returns:
            True if completed successfully, False if timeout
        """
        return self._client.wait_for_completion(
            check_endpoint="billing/admin/progress",
            completion_field="progress",
            max_field="maxProgress",
            progress_code=BatchJobCode.API_CALCULATE_USAGE_AND_PRICE.value,
            check_interval=check_interval,
            max_wait_time=timeout,
        )

    def delete_resources(self) -> dict[str, Any]:
        """Delete calculation resources for the month.

        Returns:
            API response data

        Raises:
            APIRequestException: If deletion fails
        """
        endpoint = "billing/admin/resources"
        params = {"month": self.month}
        headers = {"uuid": self.uuid}

        logger.info("Deleting calculation resources for %s", self.month)

        try:
            response = self._client.delete(endpoint, params=params, headers=headers)
            logger.info("Resources deleted successfully")
            return response
        except APIRequestException as e:
            logger.exception("Failed to delete resources: %s", e)
            raise

    def get_calculation_status(self) -> dict[str, Any]:
        """Get current calculation progress status.

        Returns:
            Progress status data

        Raises:
            APIRequestException: If status check fails
        """
        endpoint = "billing/admin/progress"

        try:
            return self._client.get(endpoint)
        except APIRequestException as e:
            logger.exception("Failed to get calculation status: %s", e)
            raise


# Backward compatibility wrapper
class Calculation:
    """Legacy wrapper for backward compatibility."""

    def __init__(self, month: str, uuid: str) -> None:
        self._manager = CalculationManager(month, uuid)
        self.month = month
        self.uuid = uuid

    def recalculation_all(self) -> None:
        """Legacy method for recalculation."""
        with contextlib.suppress(Exception):
            self._manager.recalculate_all()

    def check_stable(self) -> None:
        """Legacy method for checking calculation stability."""
        # This method is called after recalculation in the new implementation
        completed = self._manager._wait_for_calculation_completion()
        if completed:
            pass

    def delete_resources(self) -> None:
        """Legacy method for deleting resources."""
        with contextlib.suppress(Exception):
            self._manager.delete_resources()
