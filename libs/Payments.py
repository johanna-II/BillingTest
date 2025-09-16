"""Payment management for billing system."""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING, Any

from config import url

from .constants import PaymentStatus
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient

if TYPE_CHECKING:
    from .types import PaymentData

logger = logging.getLogger(__name__)


class PaymentManager:
    """Manages payment operations including inquiry, modification, and cancellation."""

    def __init__(self, month: str, uuid: str) -> None:
        """Initialize payment manager.

        Args:
            month: Target month in YYYY-MM format
            uuid: User UUID for payment operations

        Raises:
            ValidationException: If month format is invalid
        """
        self._validate_month_format(month)
        self.month = month
        self.uuid = uuid
        self._client = BillingAPIClient(url.BASE_BILLING_URL)

    def __repr__(self) -> str:
        return f"PaymentManager(month={self.month}, uuid={self.uuid})"

    @staticmethod
    def _validate_month_format(month: str) -> None:
        """Validate month format is YYYY-MM."""
        try:
            from datetime import datetime

            datetime.strptime(month, "%Y-%m")
        except ValueError:
            msg = f"Invalid month format: {month}. Expected YYYY-MM"
            raise ValidationException(
                msg
            )

    def get_payment_status(self, use_admin_api: bool = False) -> tuple[str, str]:
        """Get payment status for the month.

        Args:
            use_admin_api: Whether to use admin API (True) or console API (False)

        Returns:
            Tuple of (payment_group_id, payment_status_code)

        Raises:
            APIRequestException: If inquiry fails
        """
        if use_admin_api:
            return self._get_payment_status_admin()
        return self._get_payment_status_console()

    def _get_payment_status_admin(self) -> Tuple[str, str]:
        """Get payment status using admin API."""
        params = {
            "page": 1,
            "itemsPerPage": 10,
            "monthFrom": self.month,
            "monthTo": self.month,
            "uuid": self.uuid,
        }

        headers = {"Accept": "application/json"}

        endpoint = "billing/admin/payments"

        logger.info("Getting payment status from admin API for %s", self.month)

        try:
            response = self._client.get(endpoint, headers=headers, params=params)

            statements = response.get("statements", [])
            if not statements:
                logger.warning("No payment statements found")
                return "", ""

            # Get first statement (assuming integrated payment)
            statement = statements[0]
            payment_group_id = statement.get("paymentGroupId", "")
            payment_status = statement.get("paymentStatusCode", "")

            logger.info("Payment status: {payment_status} (Group ID: %s)", payment_group_id
            )
            return payment_group_id, payment_status

        except APIRequestException as e:
            logger.exception("Failed to get payment status from admin: %s", e)
            raise

    def _get_payment_status_console(self) -> Tuple[str, str]:
        """Get payment status using console API."""
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "lang": "kr",
            "uuid": self.uuid,
        }

        endpoint = f"billing/payments/{self.month}/statements"

        logger.info("Getting payment status from console API for %s", self.month)

        try:
            response = self._client.get(endpoint, headers=headers)

            statements = response.get("statements", [])
            if not statements:
                logger.warning("No payment statements found")
                return "", ""

            # Get first statement (assuming integrated payment)
            statement = statements[0]
            payment_group_id = statement.get("paymentGroupId", "")
            payment_status = statement.get("paymentStatusCode", "")

            logger.info("Payment status: {payment_status} (Group ID: %s)", payment_group_id
            )
            return payment_group_id, payment_status

        except APIRequestException as e:
            logger.exception("Failed to get payment status from console: %s", e)
            raise

    def change_payment_status(
        self,
        payment_group_id: str,
        target_status: PaymentStatus = PaymentStatus.REGISTERED,
    ) -> Dict[str, Any]:
        """Change payment status.

        Args:
            payment_group_id: Payment group ID to modify
            target_status: Target payment status

        Returns:
            API response data

        Raises:
            APIRequestException: If status change fails
        """
        headers = {"Accept": "application/json", "Content-type": "application/json"}

        data = {"paymentGroupId": payment_group_id}

        endpoint = f"billing/admin/payments/{self.month}/status"

        logger.info("Changing payment status for {payment_group_id} to %s", target_status.value
        )

        try:
            response = self._client.put(endpoint, headers=headers, json_data=data)
            logger.info("Successfully changed payment status for %s", self.month)
            return response
        except APIRequestException as e:
            logger.exception("Failed to change payment status: %s", e)
            raise

    def cancel_payment(self, payment_group_id: str) -> Dict[str, Any]:
        """Cancel payment.

        Args:
            payment_group_id: Payment group ID to cancel

        Returns:
            API response data

        Raises:
            APIRequestException: If cancellation fails
        """
        headers = {"Accept": "application/json;charset=UTF-8"}

        params = {"paymentGroupId": payment_group_id}

        endpoint = f"billing/admin/payments/{self.month}"

        logger.info("Cancelling payment for %s", payment_group_id)

        try:
            response = self._client.delete(endpoint, headers=headers, params=params)
            logger.info("Successfully cancelled payment for %s", self.month)
            return response
        except APIRequestException as e:
            logger.exception("Failed to cancel payment: %s", e)
            raise

    def make_payment(
        self, payment_group_id: str, retry_on_failure: bool = True, max_retries: int = 3
    ) -> Dict[str, Any]:
        """Make immediate payment.

        Args:
            payment_group_id: Payment group ID to pay
            retry_on_failure: Whether to retry on failure
            max_retries: Maximum number of retries

        Returns:
            API response data

        Raises:
            APIRequestException: If payment fails after retries
        """
        headers = {"Accept": "application/json;charset=UTF-8", "uuid": self.uuid}

        data: PaymentData = {"paymentGroupId": payment_group_id}

        endpoint = f"billing/payments/{self.month}"

        for attempt in range(max_retries):
            logger.info("Making payment for {payment_group_id} (Attempt %s)", attempt + 1
            )

            try:
                response = self._client.post(endpoint, headers=headers, json_data=data)
                logger.info("Successfully made payment for %s", self.month)
                return response
            except APIRequestException as e:
                logger.exception("Payment attempt {attempt + 1} failed: %s", e)

                if not retry_on_failure or attempt == max_retries - 1:
                    raise

                logger.info("Retrying payment...")
        return None

    def check_unpaid(self) -> int:
        """Check unpaid amount for the month.

        Returns:
            Total unpaid amount

        Raises:
            APIRequestException: If inquiry fails
        """
        headers = {"Accept": "application/json", "lang": "kr", "uuid": self.uuid}

        endpoint = f"billing/payments/{self.month}/statements/unpaid"

        logger.info("Checking unpaid amount for %s", self.month)

        try:
            response = self._client.get(endpoint, headers=headers)

            statements = response.get("statements", [])
            if not statements:
                logger.info("No unpaid statements found")
                return 0

            total_amount = statements[0].get("totalAmount", 0)
            logger.info("Unpaid amount: %s", total_amount)
            return total_amount

        except APIRequestException as e:
            logger.exception("Failed to check unpaid amount: %s", e)
            raise

    def prepare_payment(self) -> Tuple[str, str]:
        """Prepare payment by ensuring status is REGISTERED.

        Returns:
            Tuple of (payment_group_id, final_status)

        Raises:
            APIRequestException: If preparation fails
        """
        payment_group_id, payment_status = self.get_payment_status()

        if not payment_group_id:
            msg = "No payment found for the specified month"
            raise ValidationException(msg)

        if payment_status == PaymentStatus.PAID.value:
            logger.info("Payment is already paid, cancelling...")
            self.cancel_payment(payment_group_id)
            self.change_payment_status(payment_group_id, PaymentStatus.REGISTERED)
            return payment_group_id, PaymentStatus.REGISTERED.value

        if payment_status == PaymentStatus.READY.value:
            logger.info("Payment is ready, changing to registered...")
            self.change_payment_status(payment_group_id, PaymentStatus.REGISTERED)
            return payment_group_id, PaymentStatus.REGISTERED.value

        if payment_status == PaymentStatus.REGISTERED.value:
            logger.info("Payment is already registered")
            return payment_group_id, payment_status

        logger.warning("Unknown payment status: %s", payment_status)
        return payment_group_id, payment_status


# Backward compatibility wrapper
class Payments:
    """Legacy wrapper for backward compatibility."""

    def __init__(self, month: str) -> None:
        self.month = month
        self._uuid = ""
        self._projectId = ""
        self._manager = None

    def __repr__(self) -> str:
        return f"Payments(uuid: {self.uuid}, month: {self.month}, projectId: {self.projectId})"

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, uuid) -> None:
        self._uuid = uuid
        self._manager = PaymentManager(self.month, uuid) if uuid else None

    @property
    def project_id(self):
        return self._projectId

    @project_id.setter
    def project_id(self, projectId) -> None:
        self._projectId = projectId

    def inquiry_payment_admin(self):
        """Legacy method for admin payment inquiry."""
        if not self._manager:
            return "", ""

        try:
            payment_group_id, payment_status = self._manager.get_payment_status(
                use_admin_api=True
            )

            if payment_group_id:
                pass
            else:
                pass

            return payment_group_id, payment_status
        except Exception:
            return "", ""

    def inquiry_payment(self):
        """Legacy method for console payment inquiry."""
        if not self._manager:
            return "", ""

        try:
            payment_group_id, payment_status = self._manager.get_payment_status(
                use_admin_api=False
            )

            if payment_group_id:
                pass
            else:
                pass

            return payment_group_id, payment_status
        except Exception:
            return "", ""

    def change_payment(self, pgId) -> None:
        """Legacy method for changing payment status."""
        if not self._manager:
            return

        with contextlib.suppress(Exception):
            self._manager.change_payment_status(pgId)

    def cancel_payment(self, pgId) -> None:
        """Legacy method for cancelling payment."""
        if not self._manager:
            return

        with contextlib.suppress(Exception):
            self._manager.cancel_payment(pgId)

    def payment(self, pgId) -> None:
        """Legacy method for making payment."""
        if not self._manager:
            return

        with contextlib.suppress(Exception):
            self._manager.make_payment(pgId)

    def unpaid(self):
        """Legacy method for checking unpaid amount."""
        if not self._manager:
            return 0

        try:
            unpaid_amount = self._manager.check_unpaid()

            if unpaid_amount:
                pass
            else:
                pass

            return unpaid_amount
        except Exception:
            return 0
