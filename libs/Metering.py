"""Metering management for billing system."""

import calendar
import logging
from datetime import datetime
from typing import Any

from config import url

from .billing_types import MeteringData, MeteringRequest
from .constants import CounterType
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient

logger = logging.getLogger(__name__)


class MeteringManager:
    """Manages metering data submission and deletion."""

    def __init__(self, month: str, client: BillingAPIClient | None = None) -> None:
        """Initialize metering manager.

        Args:
            month: Target month in YYYY-MM format
            client: Optional API client (creates default if not provided)

        Raises:
            ValidationException: If month format is invalid
        """
        self._validate_month_format(month)
        self.month = month
        self._client = client or BillingAPIClient(url.BASE_METERING_URL)
        self._iaas_template = self._create_default_template()

    def __repr__(self) -> str:
        return f"MeteringManager(month={self.month})"

    @staticmethod
    def _validate_month_format(month: str) -> None:
        """Validate month format is YYYY-MM."""
        import re

        # First check the exact format with regex
        if not re.match(r"^\d{4}-\d{2}$", month):
            msg = f"Invalid month format: {month}. Expected YYYY-MM"
            raise ValidationException(msg)

        # Then validate it's a real date
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            msg = f"Invalid month format: {month}. Expected YYYY-MM"
            raise ValidationException(msg)

    @staticmethod
    def _create_default_template() -> MeteringRequest:
        """Create default metering template."""
        return {
            "meterList": [
                {
                    "appKey": "",
                    "counterName": "",
                    "counterType": "",
                    "counterUnit": "",
                    "counterVolume": "",
                    "parentResourceId": "test",
                    "resourceId": "test",
                    "resourceName": "test",
                    "source": "qa.billing.test",
                    "timestamp": "",
                }
            ]
        }

    def send_metering(
        self,
        app_key: str,
        counter_name: str,
        counter_type: CounterType | str,
        counter_unit: str,
        counter_volume: str,
        resource_id: str = "test",
        resource_name: str = "test",
        parent_resource_id: str = "test",
    ) -> dict[str, Any]:
        """Send metering data for an app.

        Args:
            app_key: Application key
            counter_name: Name of the counter (e.g., "compute.c2.c8m8")
            counter_type: Type of counter (DELTA or GAUGE)
            counter_unit: Unit of measurement (e.g., "HOURS", "KB")
            counter_volume: Volume to report
            resource_id: Resource identifier
            resource_name: Resource name
            parent_resource_id: Parent resource identifier

        Returns:
            API response data

        Raises:
            ValidationException: If parameters are invalid
            APIRequestException: If metering submission fails
        """
        # Normalize counter type
        counter_type_str = (
            counter_type.value
            if isinstance(counter_type, CounterType)
            else counter_type
        )

        # Validate counter type
        if counter_type_str not in [t.value for t in CounterType]:
            msg = f"Invalid counter type: {counter_type_str}"
            raise ValidationException(msg)

        # Build metering data
        metering_data: MeteringData = {
            "appKey": app_key,
            "counterName": counter_name,
            "counterType": counter_type_str,
            "counterUnit": counter_unit,
            "counterVolume": counter_volume,
            "parentResourceId": parent_resource_id,
            "resourceId": resource_id,
            "resourceName": resource_name,
            "source": "qa.billing.test",
            "timestamp": f"{self.month}-01T13:00:00.000+09:00",
        }

        request_data: MeteringRequest = {"meterList": [metering_data]}

        logger.info(
            "Sending metering data for {app_key}: {counter_name} = {counter_volume} %s",
            counter_unit,
        )

        try:
            response = self._client.post("billing/meters", json_data=request_data)
            logger.info("Successfully sent metering data for %s", self.month)
            return response
        except APIRequestException as e:
            logger.exception("Failed to send metering data: %s", e)
            raise

    def send_iaas_metering(
        self,
        counter_name: str,
        counter_unit: str,
        counter_volume: float | str,
        counter_type: CounterType | str | None = None,
        app_key: str | None = None,
        target_time: str | None = None,
        uuid: str | None = None,
        app_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Send IaaS metering data (legacy compatibility method).

        This is an alias for send_metering() for backward compatibility.
        """
        # Use instance appkey if app_key not provided (legacy pattern)
        if app_key is None:
            app_key = getattr(self, "appkey", None)
            if app_key is None:
                msg = "app_key must be provided or set as self.appkey"
                raise ValueError(msg)

        # Call send_metering with only supported parameters
        # (ignoring legacy parameters: target_time, uuid, app_id, project_id)
        return self.send_metering(
            app_key=app_key,
            counter_name=counter_name,
            counter_unit=counter_unit,
            counter_volume=str(counter_volume),
            counter_type=counter_type or CounterType.DELTA,
        )

    def delete_metering(self, app_keys: str | list[str]) -> dict[str, Any]:
        """Delete metering data for specified app keys.

        Args:
            app_keys: Single app key or list of app keys

        Returns:
            API response data

        Raises:
            APIRequestException: If deletion fails
        """
        # Normalize to list
        if isinstance(app_keys, str):
            app_keys = [app_keys]

        # Calculate date range for the month
        year, month = map(int, self.month.split("-"))
        _, last_day = calendar.monthrange(year, month)
        from_date = f"{self.month}-01"
        to_date = f"{self.month}-{last_day:02d}"

        deleted_count = 0

        for app_key in app_keys:
            logger.info("Deleting metering data for {app_key} in %s", self.month)

            params = {"appKey": app_key, "from": from_date, "to": to_date}

            try:
                self._client.delete("billing/admin/meters", params=params)
                deleted_count += 1
                logger.info("Successfully deleted metering data for %s", app_key)
            except APIRequestException as e:
                logger.exception("Failed to delete metering data for {app_key}: %s", e)
                raise

        logger.info("Deleted metering data for %s app keys", deleted_count)
        return {"deleted_count": deleted_count}

    def send_batch_metering(self, meters: list[dict[str, Any]]) -> dict[str, Any]:
        """Send batch metering data.

        Args:
            meters: List of meter data dictionaries

        Returns:
            Batch submission result
        """
        endpoint = "billing/admin/metering/batch"
        data = {"month": self.month, "meters": meters}

        try:
            return self._client.post(endpoint, json_data=data)
        except APIRequestException as e:
            logger.exception("Failed to send batch metering: %s", e)
            raise

    def get_metering_summary(self, app_key: str | None = None) -> dict[str, Any]:
        """Get metering summary.

        Args:
            app_key: Optional app key to filter by

        Returns:
            Metering summary data
        """
        endpoint = "billing/admin/metering/summary"
        params = {"month": self.month}
        if app_key:
            params["app_key"] = app_key

        try:
            return self._client.get(endpoint, params=params)
        except APIRequestException as e:
            logger.exception("Failed to get metering summary: %s", e)
            raise

    def get_metering_aggregation(self, group_by: list[str]) -> dict[str, Any]:
        """Get metering data aggregation.

        Args:
            group_by: List of fields to group by

        Returns:
            Aggregated metering data
        """
        endpoint = "billing/admin/metering/aggregate"
        params = {"month": self.month, "group_by": ",".join(group_by)}

        try:
            return self._client.get(endpoint, params=params)
        except APIRequestException as e:
            logger.exception("Failed to get metering aggregation: %s", e)
            raise

    def validate_metering(
        self,
        app_key: str,
        counter_name: str,
        counter_type: CounterType | str,
        counter_unit: str,
        counter_volume: str,
    ) -> dict[str, Any]:
        """Validate metering data before sending.

        Args:
            app_key: Application key
            counter_name: Counter name
            counter_type: Counter type
            counter_unit: Counter unit
            counter_volume: Counter volume

        Returns:
            Validation result
        """
        endpoint = "billing/admin/metering/validate"
        data = {
            "app_key": app_key,
            "counter_name": counter_name,
            "counter_type": str(counter_type),
            "counter_unit": counter_unit,
            "counter_volume": counter_volume,
        }

        try:
            return self._client.post(endpoint, json_data=data)
        except APIRequestException as e:
            logger.exception("Failed to validate metering: %s", e)
            raise

    def correct_metering(
        self, metering_id: str, corrected_volume: str, reason: str
    ) -> dict[str, Any]:
        """Correct metering data.

        Args:
            metering_id: ID of metering to correct
            corrected_volume: Corrected volume
            reason: Reason for correction

        Returns:
            Correction result
        """
        endpoint = "billing/admin/metering/correct"
        data = {
            "metering_id": metering_id,
            "corrected_volume": corrected_volume,
            "reason": reason,
        }

        try:
            return self._client.post(endpoint, json_data=data)
        except APIRequestException as e:
            logger.exception("Failed to correct metering: %s", e)
            raise
