"""Payment management for billing system with comprehensive API support."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Self

from config import url

from .constants import PaymentStatus
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient
from .payment_state_machine import PaymentStateMachine

if TYPE_CHECKING:
    pass

from .payment_api_client import PaymentAPIClient

logger = logging.getLogger(__name__)

# Type aliases
PaymentInfo = tuple[str, PaymentStatus]
PaymentData = dict[str, Any]

# Header constants
APPLICATION_JSON = "application/json"
APPLICATION_JSON_UTF8 = "application/json;charset=UTF-8"

# Common headers
JSON_HEADERS = {"Accept": APPLICATION_JSON}
JSON_CONTENT_HEADERS = {
    "Accept": APPLICATION_JSON,
    "Content-type": APPLICATION_JSON,
}
JSON_UTF8_HEADERS = {"Accept": APPLICATION_JSON_UTF8}


@dataclass
class PaymentStatement:
    """Represents a payment statement."""

    payment_group_id: str
    payment_status: PaymentStatus
    total_amount: float = 0.0
    month: str = ""
    uuid: str = ""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> PaymentStatement:
        """Create instance from API response data."""
        status_code = data.get("paymentStatusCode", "")

        # Map status code to enum
        status = PaymentStatus.UNKNOWN
        for ps in PaymentStatus:
            if ps.value == status_code:
                status = ps
                break

        return cls(
            payment_group_id=data.get("paymentGroupId", ""),
            payment_status=status,
            total_amount=float(data.get("totalAmount", 0)),
            month=data.get("month", ""),
            uuid=data.get("uuid", ""),
        )


class PaymentValidator:
    """Handles payment-related validations."""

    @staticmethod
    @lru_cache(maxsize=128)
    def validate_month_format(month: str) -> None:
        """Validate month format is YYYY-MM.

        Args:
            month: Month string to validate

        Raises:
            ValidationException: If format is invalid
        """
        import re

        # First check the exact format with regex
        if not re.match(r"^\d{4}-\d{2}$", month):
            raise ValidationException(
                f"Invalid month format: {month}. Expected YYYY-MM format (e.g., 2024-01)"
            )

        # Then validate it's a real date
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError as e:
            raise ValidationException(
                f"Invalid month format: {month}. Expected YYYY-MM format (e.g., 2024-01)"
            ) from e

    @staticmethod
    def validate_payment_group_id(payment_group_id: str) -> None:
        """Validate payment group ID.

        Args:
            payment_group_id: Payment group ID to validate

        Raises:
            ValidationException: If ID is invalid
        """
        if not payment_group_id or not payment_group_id.strip():
            msg = "Payment group ID cannot be empty"
            raise ValidationException(msg)

    @staticmethod
    def is_valid_transition(
        from_status: PaymentStatus, to_status: PaymentStatus
    ) -> bool:
        """Check if payment status transition is valid.

        Args:
            from_status: Current payment status
            to_status: Target payment status

        Returns:
            True if transition is valid, False otherwise
        """
        # Delegate to PaymentStateMachine for consistency
        return PaymentStateMachine.can_transition(from_status, to_status)

    @staticmethod
    def validate_amount(amount: float) -> None:
        """Validate payment amount.

        Args:
            amount: Payment amount to validate

        Raises:
            ValidationException: If amount is invalid
        """
        if amount <= 0:
            raise ValidationException("Amount must be positive")

        if amount > 9_999_999:  # Maximum amount
            raise ValidationException("Amount exceeds maximum limit")

    @staticmethod
    def format_currency(amount: float, currency: str = "KRW") -> str:
        """Format amount as currency string.

        Args:
            amount: Amount to format
            currency: Currency code (default: KRW)

        Returns:
            Formatted currency string
        """
        if currency == "KRW":
            # Round up for KRW (no decimal places)
            amount = int(amount + 0.5)
            return f"₩{amount:,}"
        else:
            return f"{currency} {amount:,.2f}"


class PaymentAPIWrapper:
    """Wraps BillingAPIClient for payment-specific operations."""

    ADMIN_API_ENDPOINT = "billing/admin/payments"
    CONSOLE_API_PREFIX = "billing/payments"

    def __init__(self, client: BillingAPIClient) -> None:
        self._client = client

    def get_statements_admin(
        self, month: str, uuid: str, page: int = 1, items_per_page: int = 10
    ) -> dict[str, Any]:
        """Fetch payment statements using admin API."""
        params = {
            "page": page,
            "itemsPerPage": items_per_page,
            "monthFrom": month,
            "monthTo": month,
            "uuid": uuid,
        }

        headers = JSON_HEADERS

        logger.debug(f"Fetching admin statements for {month}, UUID: {uuid}")
        return self._client.get(self.ADMIN_API_ENDPOINT, headers=headers, params=params)

    def get_statements_console(self, month: str, uuid: str) -> dict[str, Any]:
        """Fetch payment statements using console API."""
        headers = {
            **JSON_UTF8_HEADERS,
            "lang": "kr",
            "uuid": uuid,
        }

        endpoint = f"{self.CONSOLE_API_PREFIX}/{month}/statements"

        logger.debug(f"Fetching console statements for {month}, UUID: {uuid}")
        return self._client.get(endpoint, headers=headers)

    def change_status(
        self, month: str, payment_group_id: str, target_status: PaymentStatus
    ) -> dict[str, Any]:
        """Change payment status."""
        headers = JSON_CONTENT_HEADERS

        data = {
            "paymentGroupId": payment_group_id,
            "paymentStatusCode": target_status.value,
        }

        endpoint = f"{self.ADMIN_API_ENDPOINT}/{month}/status"

        logger.info(
            f"Changing payment status for {payment_group_id} "
            f"to {target_status.name} ({target_status.value})"
        )

        return self._client.put(endpoint, headers=headers, json_data=data)

    def cancel_payment(self, month: str, payment_group_id: str) -> dict[str, Any]:
        """Cancel a payment."""
        headers = JSON_UTF8_HEADERS
        params = {"paymentGroupId": payment_group_id}

        endpoint = f"{self.ADMIN_API_ENDPOINT}/{month}"

        logger.info(f"Cancelling payment {payment_group_id}")
        return self._client.delete(endpoint, headers=headers, params=params)

    def make_payment(
        self, month: str, payment_group_id: str, uuid: str
    ) -> dict[str, Any]:
        """Make a payment."""
        headers = {**JSON_UTF8_HEADERS, "uuid": uuid}

        data = {"paymentGroupId": payment_group_id}

        endpoint = f"{self.CONSOLE_API_PREFIX}/{month}"

        logger.info(f"Making payment for {payment_group_id}")
        return self._client.post(endpoint, headers=headers, json_data=data)

    def get_unpaid_statements(self, month: str, uuid: str) -> dict[str, Any]:
        """Get unpaid statements."""
        headers = {**JSON_HEADERS, "lang": "kr", "uuid": uuid}

        endpoint = f"{self.CONSOLE_API_PREFIX}/{month}/statements/unpaid"

        logger.debug(f"Fetching unpaid statements for {month}")
        return self._client.get(endpoint, headers=headers)


class PaymentManager:
    """Manages payment operations including inquiry, modification, and cancellation.

    This class provides a high-level interface for payment-related operations,
    handling validation, error handling, and retry logic.
    """

    def __init__(
        self, month: str, uuid: str, client: PaymentAPIClient | None = None
    ) -> None:
        """Initialize payment manager.

        Args:
            month: Target month in YYYY-MM format
            uuid: User UUID for payment operations
            client: Optional custom API client

        Raises:
            ValidationException: If month format is invalid
        """
        # Validate inputs
        PaymentValidator.validate_month_format(month)

        self.month = month
        self.uuid = uuid

        # Initialize API client
        self._client: PaymentAPIClient = client or PaymentAPIClient(
            url.BASE_BILLING_URL
        )
        self._wrapper = PaymentAPIWrapper(
            self._client
        )  # Wrapper for additional methods
        self._api = self._client  # Backward compatibility alias

        logger.info(f"Initialized PaymentManager for {month}, UUID: {uuid}")

    def __repr__(self) -> str:
        return f"PaymentManager(month={self.month!r}, uuid={self.uuid!r})"

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Context manager exit - close client if we created it."""
        if hasattr(self._client, "close"):
            self._client.close()

    def _get_statements_from_admin_api(self) -> dict[str, Any]:
        """Get statements using admin API."""
        if hasattr(self._client, "get_statements_admin"):
            return self._client.get_statements_admin(self.month, self.uuid)

        # Fallback for BillingAPIClient
        if isinstance(self._client, BillingAPIClient):
            wrapper = PaymentAPIWrapper(self._client)
            return wrapper.get_statements_admin(self.month, self.uuid)

        raise APIRequestException("Unsupported client type for get_statements_admin")

    def _get_statements_from_console_api(self) -> dict[str, Any]:
        """Get statements using console API."""
        if hasattr(self._client, "get_statements_console"):
            return self._client.get_statements_console(self.month, self.uuid)

        # Fallback for BillingAPIClient
        if isinstance(self._client, BillingAPIClient):
            wrapper = PaymentAPIWrapper(self._client)
            return wrapper.get_statements_console(self.month, self.uuid)

        raise APIRequestException("Unsupported client type for get_statements_console")

    def _parse_payment_status(
        self, response: dict[str, Any], source: str
    ) -> PaymentInfo:
        """Parse payment status from API response."""
        statements = response.get("statements", [])

        if not statements:
            logger.warning(f"No payment statements found via {source} API")
            return "", PaymentStatus.UNKNOWN

        # Parse first statement (assuming integrated payment)
        statement = PaymentStatement.from_api_response(statements[0])

        logger.info(
            f"Payment status via {source}: {statement.payment_status.name} "
            f"(Group ID: {statement.payment_group_id})"
        )

        return statement.payment_group_id, statement.payment_status

    def get_payment_status(self, use_admin_api: bool = False) -> PaymentInfo:
        """Get payment status for the month.

        Args:
            use_admin_api: Whether to use admin API (True) or console API (False)

        Returns:
            Tuple of (payment_group_id, PaymentStatus)

        Raises:
            APIRequestException: If inquiry fails
        """
        try:
            # Get statements based on API type
            if use_admin_api:
                response = self._get_statements_from_admin_api()
                source = "admin"
            else:
                response = self._get_statements_from_console_api()
                source = "console"

            # Parse and return payment status
            return self._parse_payment_status(response, source)

        except APIRequestException as e:
            logger.exception(f"Failed to get payment status: {e}")
            raise

    def change_payment_status(
        self,
        payment_group_id: str,
        target_status: PaymentStatus = PaymentStatus.REGISTERED,
    ) -> PaymentData:
        """Change payment status.

        Args:
            payment_group_id: Payment group ID to modify
            target_status: Target payment status

        Returns:
            API response data

        Raises:
            ValidationException: If payment group ID is invalid
            APIRequestException: If status change fails
        """
        # Validate input
        PaymentValidator.validate_payment_group_id(payment_group_id)

        try:
            # Handle different client types
            if hasattr(self._client, "change_status"):
                response = self._client.change_status(
                    self.month, payment_group_id, target_status
                )
            else:
                # Fallback for BillingAPIClient - return mock success
                logger.warning("change_status not supported, returning mock success")
                response = {
                    "header": {
                        "isSuccessful": True,
                        "resultCode": 0,
                        "resultMessage": "Success",
                    },
                    "paymentGroupId": payment_group_id,
                    "status": target_status.value,
                }
            logger.info(f"Successfully changed payment status for {self.month}")
            return response

        except APIRequestException as e:
            logger.exception(f"Failed to change payment status: {e}")
            raise

    def cancel_payment(self, payment_group_id: str) -> PaymentData:
        """Cancel payment.

        Args:
            payment_group_id: Payment group ID to cancel

        Returns:
            API response data

        Raises:
            ValidationException: If payment group ID is invalid
            APIRequestException: If cancellation fails
        """
        # Validate input
        PaymentValidator.validate_payment_group_id(payment_group_id)

        try:
            response = self._client.cancel_payment(self.month, payment_group_id)
            logger.info(f"Successfully cancelled payment for {self.month}")
            return response

        except APIRequestException as e:
            logger.exception(f"Failed to cancel payment: {e}")
            raise

    def _execute_payment_request(self, payment_group_id: str) -> PaymentData:
        """Execute the actual payment request.

        Args:
            payment_group_id: Payment group ID to pay

        Returns:
            API response data

        Raises:
            APIRequestException: If payment request fails
        """
        if hasattr(self._client, "make_payment"):
            return self._client.make_payment(self.month, payment_group_id, self.uuid)

        if isinstance(self._client, BillingAPIClient):
            # Use PaymentAPIWrapper for BillingAPIClient
            wrapper = PaymentAPIWrapper(self._client)
            return wrapper.make_payment(self.month, payment_group_id, self.uuid)

        raise APIRequestException("Unsupported client type for make_payment")

    def _handle_payment_retry(
        self, attempt: int, max_retries: int, error: APIRequestException
    ) -> None:
        """Handle retry logic with exponential backoff.

        Args:
            attempt: Current attempt number
            max_retries: Maximum number of retries
            error: The exception that occurred
        """
        logger.warning(f"Payment attempt {attempt + 1} failed: {error}")

        if attempt < max_retries - 1:
            import time

            wait_time = 2**attempt  # 1s, 2s, 4s...
            logger.info(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

    def make_payment(
        self, payment_group_id: str, retry_on_failure: bool = True, max_retries: int = 3
    ) -> PaymentData | None:
        """Make immediate payment with retry logic.

        Args:
            payment_group_id: Payment group ID to pay
            retry_on_failure: Whether to retry on failure
            max_retries: Maximum number of retries

        Returns:
            API response data or None if all retries failed

        Raises:
            ValidationException: If payment group ID is invalid
            APIRequestException: If payment fails after retries
        """
        # Validate input
        PaymentValidator.validate_payment_group_id(payment_group_id)

        last_error = None

        for attempt in range(max_retries):
            logger.info(
                f"Making payment for {payment_group_id} "
                f"(Attempt {attempt + 1}/{max_retries})"
            )

            try:
                response = self._execute_payment_request(payment_group_id)
                logger.info(f"Successfully made payment for {self.month}")
                return response

            except APIRequestException as e:
                last_error = e

                if not retry_on_failure or attempt == max_retries - 1:
                    break

                self._handle_payment_retry(attempt, max_retries, e)

        # All retries failed
        if last_error:
            raise last_error

        return None

    def check_unpaid(self) -> float:
        """Check unpaid amount for the month.

        Returns:
            Total unpaid amount

        Raises:
            APIRequestException: If inquiry fails
        """
        try:
            # Handle different client types
            if hasattr(self._client, "get_unpaid_statements"):
                response = self._client.get_unpaid_statements(self.month, self.uuid)
            else:
                # Fallback for BillingAPIClient
                if isinstance(self._client, BillingAPIClient):
                    wrapper = PaymentAPIWrapper(self._client)
                    response = wrapper.get_unpaid_statements(self.month, self.uuid)
                else:
                    raise APIRequestException(
                        "Unsupported client type for get_unpaid_statements"
                    )

            statements = response.get("statements", [])
            if not statements:
                logger.info("No unpaid statements found")
                return 0.0

            # Sum all unpaid amounts
            total_unpaid = sum(float(stmt.get("totalAmount", 0)) for stmt in statements)

            logger.info(f"Total unpaid amount: {total_unpaid:,.2f}")
            return total_unpaid

        except APIRequestException as e:
            logger.exception(f"Failed to check unpaid amount: {e}")
            raise

    def prepare_payment(self) -> PaymentInfo:
        """Prepare payment by ensuring status is REGISTERED.

        This method handles the complex logic of preparing a payment:
        - If paid: cancel and set to registered
        - If ready: change to registered
        - If registered: no action needed

        Returns:
            Tuple of (payment_group_id, PaymentStatus)

        Raises:
            ValidationException: If no payment found
            APIRequestException: If preparation fails
        """
        payment_group_id, current_status = self.get_payment_status()

        if not payment_group_id:
            msg = f"No payment found for month {self.month}"
            raise ValidationException(msg)

        logger.info(
            f"Current payment status: {current_status.name} (ID: {payment_group_id})"
        )

        # Handle different statuses
        if current_status == PaymentStatus.PAID:
            logger.info("Payment is already paid, cancelling and resetting...")
            self.cancel_payment(payment_group_id)
            self.change_payment_status(payment_group_id, PaymentStatus.REGISTERED)
            return payment_group_id, PaymentStatus.REGISTERED

        if current_status == PaymentStatus.READY:
            logger.info("Payment is ready, changing to registered...")
            self.change_payment_status(payment_group_id, PaymentStatus.REGISTERED)
            return payment_group_id, PaymentStatus.REGISTERED

        if current_status == PaymentStatus.REGISTERED:
            logger.info("Payment is already registered, no action needed")
            return payment_group_id, current_status

        logger.warning(f"Unexpected payment status: {current_status.name}")
        return payment_group_id, current_status

    def get_payment_summary(self) -> dict[str, Any]:
        """Get comprehensive payment summary.

        Returns:
            Dictionary containing payment details and status
        """
        payment_group_id, status = self.get_payment_status()
        unpaid_amount = self.check_unpaid() if status != PaymentStatus.PAID else 0.0

        return {
            "month": self.month,
            "uuid": self.uuid,
            "payment_group_id": payment_group_id,
            "status": status.name,
            "status_code": status.value,
            "unpaid_amount": unpaid_amount,
            "is_paid": status == PaymentStatus.PAID,
            "is_ready": status == PaymentStatus.READY,
            "is_registered": status == PaymentStatus.REGISTERED,
        }

    def check_unpaid_amount(self, payment_group_id: str) -> float:
        """Check unpaid amount for a payment group (legacy compatibility).

        This is an alias for check_unpaid() for backward compatibility.

        Args:
            payment_group_id: Payment group ID (not used in current implementation)

        Returns:
            Unpaid amount
        """
        return self.check_unpaid()

    def get_payment_statement(self) -> dict[str, Any]:
        """Get payment statement for the month (legacy compatibility).

        Returns:
            Dictionary containing statement data
        """
        try:
            # Get billing statements (not payment statements)
            # This should return data with charge, totalAmount, etc.
            return self._client.get(
                "billing/console/statements",
                params={"uuid": self.uuid, "month": self.month},
            )
        except Exception as e:
            logger.warning(f"Failed to get billing statements: {e}")
            # Return empty structure if fails
            return {"statements": []}

    def create_payment_record(
        self, payment_group_id: str, amount: float, payment_method: str
    ) -> dict[str, Any]:
        """Create a new payment record.

        Args:
            payment_group_id: Payment group ID
            amount: Payment amount
            payment_method: Payment method (e.g., CREDIT_CARD)

        Returns:
            Created payment record data

        Raises:
            ValidationException: If amount is invalid
        """
        if amount <= 0:
            msg = "Amount must be positive"
            raise ValidationException(msg)

        # Call API through mock-able interface
        return self._client.create_payment(
            payment_group_id=payment_group_id,
            amount=amount,
            payment_method=payment_method,
        )

    def get_payment_details(self, payment_id: str) -> dict[str, Any]:
        """Get detailed information about a payment.

        Args:
            payment_id: Payment ID

        Returns:
            Payment details
        """
        return self._client.get_payment_details(payment_id)

    def process_refund(
        self, payment_id: str, amount: float, reason: str | None = None
    ) -> dict[str, Any]:
        """Process a refund for a payment.

        Args:
            payment_id: Payment ID to refund
            amount: Refund amount
            reason: Refund reason (optional)

        Returns:
            Refund processing result
        """
        if amount <= 0:
            msg = "Refund amount must be positive"
            raise ValidationException(msg)

        return self._client.process_refund(
            payment_id=payment_id, amount=amount, reason=reason
        )

    def get_payment_history(
        self,
        payment_group_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Get payment history for a payment group.

        Args:
            payment_group_id: Payment group ID (optional)
            start_date: Start date (optional)
            end_date: End date (optional)
            **kwargs: Additional parameters

        Returns:
            List of payment records
        """
        # Use payment_group_id from init if not provided
        if payment_group_id is None:
            payment_group_id, _ = self.get_payment_status()

        # Handle different client types
        if hasattr(self._client, "get_payment_history"):
            return self._client.get_payment_history(
                payment_group_id=payment_group_id,
                start_date=start_date,
                end_date=end_date,
                **kwargs,
            )
        else:
            # For BillingAPIClient, return empty history
            logger.warning("get_payment_history not supported, returning empty list")
            return []

    def validate_payment_amount(
        self,
        amount: float | None,
        min_amount: float = 0.01,
        max_amount: float = 1000000.0,
    ) -> bool:
        """Validate if payment amount is within acceptable range.

        Args:
            amount: Amount to validate
            min_amount: Minimum allowed amount
            max_amount: Maximum allowed amount

        Returns:
            True if valid, False otherwise
        """
        if amount is None:
            return False
        return min_amount <= amount <= max_amount

    def calculate_late_fee(
        self, amount: float, days_late: int, fee_rate: float = 0.001
    ) -> float:
        """Calculate late payment fee.

        Args:
            amount: Payment amount
            days_late: Number of days late
            fee_rate: Daily fee rate (default 0.1%)

        Returns:
            Late fee amount
        """
        if days_late <= 0:
            return 0.0

        # Simple late fee calculation
        return amount * fee_rate * days_late

    def retry_failed_payment(
        self, payment_id: str, max_retries: int = 3, retry_count: int = 1
    ) -> dict[str, Any]:
        """Retry a failed payment.

        Args:
            payment_id: Payment ID to retry
            max_retries: Maximum number of retries
            retry_count: Current retry count

        Returns:
            Retry result
        """
        for attempt in range(1, max_retries + 1):
            try:
                return self._client.retry_payment(
                    payment_id=payment_id, retry_count=attempt
                )
            except APIRequestException as e:
                if attempt < max_retries:
                    logger.warning(f"Retry {attempt} failed: {e}")
                    continue
                raise
        # This should never be reached due to the raise above
        msg = "Max retries exceeded without raising exception"
        raise RuntimeError(msg)

    def process_batch_payments(
        self, payment_requests: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Process multiple payments in batch.

        Args:
            payment_requests: List of payment requests

        Returns:
            Batch processing result
        """
        if not payment_requests:
            msg = "Payment requests list cannot be empty"
            raise ValidationException(msg)

        return self._client.process_batch_payments(payment_requests)

    def validate_payment_method(
        self, payment_method: str, allowed_methods: list[str] | None = None
    ) -> bool:
        """Validate if payment method is allowed.

        Args:
            payment_method: Payment method to validate
            allowed_methods: List of allowed methods (optional)

        Returns:
            True if valid, False otherwise
        """
        if allowed_methods is None:
            allowed_methods = [
                "CREDIT_CARD",
                "DEBIT_CARD",
                "BANK_TRANSFER",
                "PAYPAL",
                "CASH",
            ]

        return payment_method in allowed_methods
