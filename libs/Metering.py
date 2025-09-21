"""Metering management for billing system."""

import calendar
import contextlib
import logging
from datetime import datetime
from typing import Any

from config import url

from .constants import CounterType
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient
from .types import MeteringData, MeteringRequest

logger = logging.getLogger(__name__)


class MeteringManager:
    """Manages metering data submission and deletion."""

    def __init__(self, month: str) -> None:
        """Initialize metering manager.

        Args:
            month: Target month in YYYY-MM format

        Raises:
            ValidationException: If month format is invalid
        """
        self._validate_month_format(month)
        self.month = month
        self._client = BillingAPIClient(url.BASE_METERING_URL)
        self._iaas_template = self._create_default_template()

    def __repr__(self) -> str:
        return f"MeteringManager(month={self.month})"

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

        logger.info("Sending metering data for {app_key}: {counter_name} = {counter_volume} %s", counter_unit
        )

        try:
            response = self._client.post("billing/meters", json_data=request_data)
            logger.info("Successfully sent metering data for %s", self.month)
            return response
        except APIRequestException as e:
            logger.exception("Failed to send metering data: %s", e)
            raise

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

    def send_batch_metering(
        self, app_key: str, metering_items: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Send multiple metering entries for an app.

        Args:
            app_key: Application key
            metering_items: List of metering items, each containing:
                - counter_name: Name of the counter
                - counter_type: Type of counter (DELTA or GAUGE)
                - counter_unit: Unit of measurement
                - counter_volume: Volume to report

        Returns:
            API response data

        Raises:
            APIRequestException: If any submission fails
        """
        results = []

        for item in metering_items:
            try:
                self.send_metering(
                    app_key=app_key,
                    counter_name=item["counter_name"],
                    counter_type=item["counter_type"],
                    counter_unit=item["counter_unit"],
                    counter_volume=item["counter_volume"],
                )
                results.append({"success": True, "counter": item["counter_name"]})
            except APIRequestException as e:
                results.append(
                    {"success": False, "counter": item["counter_name"], "error": str(e)}
                )
                logger.exception("Failed to send metering for %s: %s", item['counter_name'], e)

        return {"results": results}


# Backward compatibility wrapper
class Metering:
    """Legacy wrapper for backward compatibility."""

    def __init__(self, month: str) -> None:
        self._manager = MeteringManager(month)
        self.month = month
        self._appkey = ""
        self._iaas_template = self._manager._iaas_template

    def __repr__(self) -> str:
        return f"Metering(month: {self.month}, appkey: {self.appkey}, iaas_template: {self._iaas_template})"

    @property
    def appkey(self):
        return self._appkey

    @appkey.setter
    def appkey(self, appkey) -> None:
        self._appkey = appkey

    def delete_metering(self) -> None:
        """Legacy method for deleting metering."""
        try:
            # Assume self.appkey is a list in legacy code
            app_keys = self.appkey if isinstance(self.appkey, list) else [self.appkey]
            self._manager.delete_metering(app_keys)
        except Exception:
            pass

    def send_iaas_metering(self, **kwargs) -> None:
        """Legacy method for sending metering."""
        with contextlib.suppress(Exception):
            self._manager.send_metering(
                app_key=self.appkey,
                counter_name=kwargs.get("counter_name", ""),
                counter_type=kwargs.get("counter_type", ""),
                counter_unit=kwargs.get("counter_unit", ""),
                counter_volume=kwargs.get("counter_volume", ""),
            )
