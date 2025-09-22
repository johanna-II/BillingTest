"""Payment management for billing system with comprehensive API support."""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple, Union

from config import url

from .constants import PaymentStatus
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient

logger = logging.getLogger(__name__)

# Type aliases
PaymentInfo = Tuple[str, PaymentStatus]
PaymentData = Dict[str, Any]


@dataclass
class PaymentStatement:
    """Represents a payment statement."""
    payment_group_id: str
    payment_status: PaymentStatus
    total_amount: float = 0.0
    month: str = ""
    uuid: str = ""
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'PaymentStatement':
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
            uuid=data.get("uuid", "")
        )


class PaymentValidator:
    """Handles payment-related validations."""
    
    @staticmethod
    @lru_cache(maxsize=128)
    def validate_month_format(month: str) -> None:
        """
        Validate month format is YYYY-MM.
        
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
        """
        Validate payment group ID.
        
        Args:
            payment_group_id: Payment group ID to validate
            
        Raises:
            ValidationException: If ID is invalid
        """
        if not payment_group_id or not payment_group_id.strip():
            raise ValidationException("Payment group ID cannot be empty")


class PaymentAPIClient:
    """Handles API communication for payments."""
    
    ADMIN_API_ENDPOINT = "billing/admin/payments"
    CONSOLE_API_PREFIX = "billing/payments"
    
    def __init__(self, client: BillingAPIClient):
        self._client = client
    
    def get_statements_admin(
        self,
        month: str,
        uuid: str,
        page: int = 1,
        items_per_page: int = 10
    ) -> Dict[str, Any]:
        """Fetch payment statements using admin API."""
        params = {
            "page": page,
            "itemsPerPage": items_per_page,
            "monthFrom": month,
            "monthTo": month,
            "uuid": uuid,
        }
        
        headers = {"Accept": "application/json"}
        
        logger.debug(f"Fetching admin statements for {month}, UUID: {uuid}")
        return self._client.get(self.ADMIN_API_ENDPOINT, headers=headers, params=params)
    
    def get_statements_console(self, month: str, uuid: str) -> Dict[str, Any]:
        """Fetch payment statements using console API."""
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "lang": "kr",
            "uuid": uuid,
        }
        
        endpoint = f"{self.CONSOLE_API_PREFIX}/{month}/statements"
        
        logger.debug(f"Fetching console statements for {month}, UUID: {uuid}")
        return self._client.get(endpoint, headers=headers)
    
    def change_status(
        self,
        month: str,
        payment_group_id: str,
        target_status: PaymentStatus
    ) -> Dict[str, Any]:
        """Change payment status."""
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json"
        }
        
        data = {
            "paymentGroupId": payment_group_id,
            "paymentStatusCode": target_status.value
        }
        
        endpoint = f"{self.ADMIN_API_ENDPOINT}/{month}/status"
        
        logger.info(
            f"Changing payment status for {payment_group_id} "
            f"to {target_status.name} ({target_status.value})"
        )
        
        return self._client.put(endpoint, headers=headers, json_data=data)
    
    def cancel_payment(self, month: str, payment_group_id: str) -> Dict[str, Any]:
        """Cancel a payment."""
        headers = {"Accept": "application/json;charset=UTF-8"}
        params = {"paymentGroupId": payment_group_id}
        
        endpoint = f"{self.ADMIN_API_ENDPOINT}/{month}"
        
        logger.info(f"Cancelling payment {payment_group_id}")
        return self._client.delete(endpoint, headers=headers, params=params)
    
    def make_payment(
        self,
        month: str,
        payment_group_id: str,
        uuid: str
    ) -> Dict[str, Any]:
        """Make a payment."""
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "uuid": uuid
        }
        
        data = {"paymentGroupId": payment_group_id}
        
        endpoint = f"{self.CONSOLE_API_PREFIX}/{month}"
        
        logger.info(f"Making payment for {payment_group_id}")
        return self._client.post(endpoint, headers=headers, json_data=data)
    
    def get_unpaid_statements(self, month: str, uuid: str) -> Dict[str, Any]:
        """Get unpaid statements."""
        headers = {
            "Accept": "application/json",
            "lang": "kr",
            "uuid": uuid
        }
        
        endpoint = f"{self.CONSOLE_API_PREFIX}/{month}/statements/unpaid"
        
        logger.debug(f"Fetching unpaid statements for {month}")
        return self._client.get(endpoint, headers=headers)


class PaymentManager:
    """
    Manages payment operations including inquiry, modification, and cancellation.
    
    This class provides a high-level interface for payment-related operations,
    handling validation, error handling, and retry logic.
    """

    def __init__(self, month: str, uuid: str, client: Optional[BillingAPIClient] = None) -> None:
        """
        Initialize payment manager.

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
        self._client = client or BillingAPIClient(url.BASE_BILLING_URL)
        self._api = PaymentAPIClient(self._client)
        
        logger.info(f"Initialized PaymentManager for {month}, UUID: {uuid}")

    def __repr__(self) -> str:
        return f"PaymentManager(month={self.month!r}, uuid={self.uuid!r})"
    
    def __enter__(self) -> 'PaymentManager':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close client if we created it."""
        if hasattr(self._client, 'close'):
            self._client.close()

    def get_payment_status(self, use_admin_api: bool = False) -> PaymentInfo:
        """
        Get payment status for the month.

        Args:
            use_admin_api: Whether to use admin API (True) or console API (False)

        Returns:
            Tuple of (payment_group_id, PaymentStatus)

        Raises:
            APIRequestException: If inquiry fails
        """
        try:
            # Choose API based on parameter
            if use_admin_api:
                response = self._api.get_statements_admin(self.month, self.uuid)
                source = "admin"
            else:
                response = self._api.get_statements_console(self.month, self.uuid)
                source = "console"
            
            # Extract statements
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
            
        except APIRequestException as e:
            logger.exception(f"Failed to get payment status: {e}")
            raise

    def change_payment_status(
        self,
        payment_group_id: str,
        target_status: PaymentStatus = PaymentStatus.REGISTERED,
    ) -> PaymentData:
        """
        Change payment status.

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
            response = self._api.change_status(self.month, payment_group_id, target_status)
            logger.info(f"Successfully changed payment status for {self.month}")
            return response
            
        except APIRequestException as e:
            logger.exception(f"Failed to change payment status: {e}")
            raise

    def cancel_payment(self, payment_group_id: str) -> PaymentData:
        """
        Cancel payment.

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
            response = self._api.cancel_payment(self.month, payment_group_id)
            logger.info(f"Successfully cancelled payment for {self.month}")
            return response
            
        except APIRequestException as e:
            logger.exception(f"Failed to cancel payment: {e}")
            raise

    def make_payment(
        self,
        payment_group_id: str,
        retry_on_failure: bool = True,
        max_retries: int = 3
    ) -> Optional[PaymentData]:
        """
        Make immediate payment with retry logic.

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
                response = self._api.make_payment(self.month, payment_group_id, self.uuid)
                logger.info(f"Successfully made payment for {self.month}")
                return response
                
            except APIRequestException as e:
                last_error = e
                logger.warning(f"Payment attempt {attempt + 1} failed: {e}")
                
                if not retry_on_failure or attempt == max_retries - 1:
                    break
                
                # Exponential backoff for retries
                if attempt < max_retries - 1:
                    import time
                    wait_time = 2 ** attempt  # 1s, 2s, 4s...
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        # All retries failed
        if last_error:
            raise last_error
        
        return None

    def check_unpaid(self) -> float:
        """
        Check unpaid amount for the month.

        Returns:
            Total unpaid amount

        Raises:
            APIRequestException: If inquiry fails
        """
        try:
            response = self._api.get_unpaid_statements(self.month, self.uuid)
            
            statements = response.get("statements", [])
            if not statements:
                logger.info("No unpaid statements found")
                return 0.0
            
            # Sum all unpaid amounts
            total_unpaid = sum(
                float(stmt.get("totalAmount", 0))
                for stmt in statements
            )
            
            logger.info(f"Total unpaid amount: {total_unpaid:,.2f}")
            return total_unpaid
            
        except APIRequestException as e:
            logger.exception(f"Failed to check unpaid amount: {e}")
            raise

    def prepare_payment(self) -> PaymentInfo:
        """
        Prepare payment by ensuring status is REGISTERED.
        
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
            raise ValidationException(
                f"No payment found for month {self.month}"
            )
        
        logger.info(
            f"Current payment status: {current_status.name} "
            f"(ID: {payment_group_id})"
        )
        
        # Handle different statuses
        if current_status == PaymentStatus.PAID:
            logger.info("Payment is already paid, cancelling and resetting...")
            self.cancel_payment(payment_group_id)
            self.change_payment_status(payment_group_id, PaymentStatus.REGISTERED)
            return payment_group_id, PaymentStatus.REGISTERED
            
        elif current_status == PaymentStatus.READY:
            logger.info("Payment is ready, changing to registered...")
            self.change_payment_status(payment_group_id, PaymentStatus.REGISTERED)
            return payment_group_id, PaymentStatus.REGISTERED
            
        elif current_status == PaymentStatus.REGISTERED:
            logger.info("Payment is already registered, no action needed")
            return payment_group_id, current_status
            
        else:
            logger.warning(f"Unexpected payment status: {current_status.name}")
            return payment_group_id, current_status
    
    def get_payment_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive payment summary.
        
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


# Backward compatibility wrapper - deprecated
class Payments:
    """
    Legacy wrapper for backward compatibility.
    
    .. deprecated:: 2.0
        Use PaymentManager directly instead.
    """

    def __init__(self, month: str) -> None:
        warnings.warn(
            "Payments class is deprecated. Use PaymentManager directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.month = month
        self._uuid = ""
        self._projectId = ""
        self._manager: Optional[PaymentManager] = None

    def __repr__(self) -> str:
        return f"Payments(month={self.month!r}, uuid={self._uuid!r})"

    @property
    def uuid(self) -> str:
        return self._uuid

    @uuid.setter
    def uuid(self, value: str) -> None:
        self._uuid = value
        self._manager = PaymentManager(self.month, value) if value else None

    @property
    def projectId(self) -> str:
        return self._projectId

    @projectId.setter
    def projectId(self, value: str) -> None:
        self._projectId = value

    # Legacy method mappings
    def inquiry_payment_admin(self) -> Tuple[str, str]:
        """Legacy method for admin payment inquiry."""
        if not self._manager:
            return "", ""
        
        try:
            group_id, status = self._manager.get_payment_status(use_admin_api=True)
            return group_id, status.value
        except Exception as e:
            logger.exception(f"Legacy inquiry_payment_admin failed: {e}")
            return "", ""

    def inquiry_payment(self) -> Tuple[str, str]:
        """Legacy method for console payment inquiry."""
        if not self._manager:
            return "", ""
        
        try:
            group_id, status = self._manager.get_payment_status(use_admin_api=False)
            return group_id, status.value
        except Exception as e:
            logger.exception(f"Legacy inquiry_payment failed: {e}")
            return "", ""

    def change_payment(self, pgId: str) -> None:
        """Legacy method for changing payment status."""
        if self._manager:
            try:
                self._manager.change_payment_status(pgId)
            except Exception as e:
                logger.exception(f"Legacy change_payment failed: {e}")

    def cancel_payment(self, pgId: str) -> None:
        """Legacy method for cancelling payment."""
        if self._manager:
            try:
                self._manager.cancel_payment(pgId)
            except Exception as e:
                logger.exception(f"Legacy cancel_payment failed: {e}")

    def payment(self, pgId: str) -> None:
        """Legacy method for making payment."""
        if self._manager:
            try:
                self._manager.make_payment(pgId)
            except Exception as e:
                logger.exception(f"Legacy payment failed: {e}")

    def unpaid(self) -> float:
        """Legacy method for checking unpaid amount."""
        if not self._manager:
            return 0.0
        
        try:
            return self._manager.check_unpaid()
        except Exception as e:
            logger.exception(f"Legacy unpaid failed: {e}")
            return 0.0