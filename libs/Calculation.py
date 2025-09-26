"""Calculation management for billing system."""

import logging
from typing import Any

from config import url

from .exceptions import APIRequestException
from .http_client import BillingAPIClient

logger = logging.getLogger(__name__)


class CalculationManager:
    """Manages billing calculations and resource cleanup."""

    def __init__(
        self, month: str, uuid: str, client: BillingAPIClient | None = None
    ) -> None:
        """Initialize calculation manager.

        Args:
            month: Target month in YYYY-MM format
            uuid: User UUID for calculations
            client: Optional HTTP client for API requests
        """
        self.month = month
        self.uuid = uuid
        self._client = client or BillingAPIClient(url.BASE_BILLING_URL)

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
                logger.warning(
                    "Recalculation did not complete within %s seconds", timeout
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
        result = self._client.wait_for_completion(
            check_endpoint=f"billing/admin/progress?month={self.month}&uuid={self.uuid}",
            status_field="status",
            success_value="COMPLETED",
            timeout=timeout,
            check_interval=check_interval,
        )
        # Convert result to bool - assuming success if no exception
        return bool(result)

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

    def calculate_with_filters(
        self,
        projects: list[str] | None = None,
        services: list[str] | None = None,
        exclude_zero_usage: bool = False,
    ) -> dict[str, Any]:
        """Calculate with specific filters.

        Args:
            projects: List of project IDs to include
            services: List of services to include
            exclude_zero_usage: Whether to exclude zero usage items

        Returns:
            Filtered calculation result
        """
        endpoint = "billing/admin/calculations/filtered"
        data = {
            "month": self.month,
            "uuid": self.uuid,
            "filters": {
                "projects": projects or [],
                "services": services or [],
                "exclude_zero_usage": exclude_zero_usage,
            },
        }

        try:
            response = self._client.post(endpoint, json_data=data)
            logger.info("Filtered calculation completed")
            return response
        except APIRequestException as e:
            logger.exception("Failed to calculate with filters: %s", e)
            raise

    def incremental_calculation(self, since_timestamp: str) -> dict[str, Any]:
        """Perform incremental calculation since timestamp.

        Args:
            since_timestamp: ISO format timestamp

        Returns:
            Incremental calculation result
        """
        endpoint = "billing/admin/calculations/incremental"
        data = {
            "month": self.month,
            "uuid": self.uuid,
            "since_timestamp": since_timestamp,
        }

        try:
            response = self._client.post(endpoint, json_data=data)
            logger.info("Incremental calculation completed")
            return response
        except APIRequestException as e:
            logger.exception("Failed incremental calculation: %s", e)
            raise

    def calculate_specific_items(self, items: list[str]) -> dict[str, Any]:
        """Calculate specific items only.

        Args:
            items: List of item IDs to calculate

        Returns:
            Calculation result for specific items
        """
        endpoint = "billing/admin/calculations/items"
        data = {"month": self.month, "uuid": self.uuid, "items": items}

        try:
            response = self._client.post(endpoint, json_data=data)
            logger.info("Calculated %d specific items", len(items))
            return response
        except APIRequestException as e:
            logger.exception("Failed to calculate specific items: %s", e)
            raise

    def get_calculation_status(self, calculation_id: str) -> dict[str, Any]:
        """Get status of specific calculation.

        Args:
            calculation_id: ID of the calculation

        Returns:
            Calculation status
        """
        endpoint = "billing/admin/calculations/status"
        params = {"calculation_id": calculation_id, "month": self.month}

        try:
            return self._client.get(endpoint, params=params)
        except APIRequestException as e:
            logger.exception("Failed to get calculation status: %s", e)
            raise
