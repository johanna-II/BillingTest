"""Credit management for billing system with comprehensive API support."""

from __future__ import annotations

import logging
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Self

from config import url

from .constants import CreditType
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient

logger = logging.getLogger(__name__)

# Type aliases
CreditAmount = int | float
CreditData = dict[str, Any]
CreditList = list[dict[str, Any]]


class CreditOperation(str, Enum):
    """Credit operation types."""

    GRANT = "grant"
    USE = "use"
    CANCEL = "cancel"
    REFUND = "refund"


@dataclass
class CreditRequest:
    """Represents a credit request."""

    campaign_id: str
    amount: CreditAmount
    credit_name: str = "Test Credit"
    expiration_period: int = 1
    expiration_date_from: str | None = None
    expiration_date_to: str | None = None
    uuid_list: list[str] = field(default_factory=list)
    email_list: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate and set defaults after initialization."""
        # Set default dates if not provided
        if not self.expiration_date_from:
            self.expiration_date_from = datetime.now().strftime("%Y-%m-%d")

        if not self.expiration_date_to:
            end_date = datetime.now() + timedelta(days=365 * self.expiration_period)
            self.expiration_date_to = end_date.strftime("%Y-%m-%d")

        # Validate amount
        if self.amount <= 0:
            msg = f"Credit amount must be positive: {self.amount}"
            raise ValidationException(msg)

    def to_api_format(self) -> dict[str, Any]:
        """Convert to API request format."""
        data = {
            "credit": int(self.amount),
            "creditName": self.credit_name,
            "expirationDateFrom": self.expiration_date_from,
            "expirationDateTo": self.expiration_date_to,
            "expirationPeriod": self.expiration_period,
            "uuidList": self.uuid_list,
            "emailList": self.email_list,
        }

        # Add credit type if available
        if hasattr(self, "credit_type"):
            data["creditType"] = self.credit_type

        return data


@dataclass
class CreditHistory:
    """Represents credit history entry."""

    credit_type: CreditType
    amount: CreditAmount
    balance: CreditAmount
    transaction_date: str
    description: str
    campaign_id: str | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> CreditHistory:
        """Create instance from API response."""
        return cls(
            credit_type=CreditType(data.get("creditType", "FREE")),
            amount=float(data.get("amount", 0)),
            balance=float(data.get("balance", 0)),
            transaction_date=data.get("transactionDate", ""),
            description=data.get("description", ""),
            campaign_id=data.get("campaignId"),
        )


class CreditAPIClient:
    """Handles API communication for credit operations."""

    COUPON_ENDPOINT = "billing/coupons/{coupon_code}"
    CAMPAIGN_CREDIT_ENDPOINT = "billing/admin/campaign/{campaign_id}/credits"
    CREDIT_HISTORY_ENDPOINT = "billing/credits/history"

    def __init__(self, client: BillingAPIClient) -> None:
        self._client = client

    def grant_coupon(self, coupon_code: str, uuid: str) -> CreditData:
        """Grant coupon-based credit."""
        headers = {"Accept": "application/json;charset=UTF-8", "uuid": uuid}

        endpoint = self.COUPON_ENDPOINT.format(coupon_code=coupon_code)

        logger.debug(f"Granting coupon credit: {coupon_code}")
        return self._client.post(endpoint, headers=headers)

    def grant_campaign_credit(
        self, campaign_id: str, credit_request: CreditRequest, uuid: str
    ) -> CreditData:
        """Grant campaign-based credit."""
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "Content-Type": "application/json",
            "uuid": uuid,
        }

        endpoint = self.CAMPAIGN_CREDIT_ENDPOINT.format(campaign_id=campaign_id)
        data = credit_request.to_api_format()

        logger.debug(
            f"Granting campaign credit: {campaign_id}, amount: {credit_request.amount}"
        )
        return self._client.post(endpoint, headers=headers, json_data=data)

    def get_credit_history(
        self,
        uuid: str,
        credit_type: CreditType,
        page: int = 1,
        items_per_page: int = 100,
    ) -> CreditData:
        """Get credit history."""
        params = {
            "uuid": uuid,
            "creditType": credit_type.value,
            "page": page,
            "itemsPerPage": items_per_page,
        }

        headers = {"Accept": "application/json;charset=UTF-8"}

        logger.debug(f"Fetching credit history: type={credit_type.value}, page={page}")
        return self._client.get(
            self.CREDIT_HISTORY_ENDPOINT, headers=headers, params=params
        )

    def cancel_credit(self, campaign_id: str, reason: str = "test") -> CreditData:
        """Cancel credit for a campaign."""
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "Content-Type": "application/json",
        }

        params = {"reason": reason}
        endpoint = self.CAMPAIGN_CREDIT_ENDPOINT.format(campaign_id=campaign_id)

        logger.debug(f"Cancelling credit for campaign: {campaign_id}")
        return self._client.delete(endpoint, headers=headers, params=params)


class CreditCalculator:
    """Handles credit calculations and validations."""

    @staticmethod
    def calculate_total_from_history(
        credit_histories: list[CreditHistory],
    ) -> CreditAmount:
        """Calculate total credit from history entries."""
        return sum(history.amount for history in credit_histories)

    @staticmethod
    def validate_credit_amount(amount: CreditAmount) -> None:
        """Validate credit amount."""
        if amount <= 0:
            msg = f"Credit amount must be positive: {amount}"
            raise ValidationException(msg)

        if amount > 1_000_000:  # Maximum credit limit
            msg = f"Credit amount exceeds maximum limit: {amount}"
            raise ValidationException(msg)

    @staticmethod
    def calculate_expiration_dates(months: int = 12) -> tuple[str, str]:
        """Calculate expiration dates based on months."""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30 * months)

        return (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))


class CreditManager:
    """Manages credit operations including granting, inquiry, and cancellation.

    This class provides a high-level interface for credit-related operations,
    handling validation, error handling, and complex business logic.
    """

    # Default values
    DEFAULT_CREDIT_NAME = "QA Billing Test Credit"
    DEFAULT_EXPIRATION_MONTHS = 12

    def __init__(self, uuid: str, client: BillingAPIClient | None = None) -> None:
        """Initialize credit manager.

        Args:
            uuid: User UUID for credit operations
            client: Optional custom API client
        """
        if not uuid:
            msg = "UUID cannot be empty"
            raise ValidationException(msg)

        self.uuid = uuid
        self._client = client or BillingAPIClient(url.BASE_BILLING_URL)
        self._api = CreditAPIClient(self._client)

        logger.info(f"Initialized CreditManager for UUID: {uuid}")

    def __repr__(self) -> str:
        return f"CreditManager(uuid={self.uuid!r})"

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

    def grant_coupon_credit(self, coupon_code: str) -> CreditData:
        """Grant coupon-based credit to user.

        Args:
            coupon_code: Code of the coupon to apply

        Returns:
            API response data

        Raises:
            ValidationException: If coupon code is invalid
            APIRequestException: If credit grant fails
        """
        if not coupon_code or not coupon_code.strip():
            msg = "Coupon code cannot be empty"
            raise ValidationException(msg)

        logger.info(f"Granting coupon credit: {coupon_code}")

        try:
            response = self._api.grant_coupon(coupon_code, self.uuid)
            logger.info(f"Successfully granted coupon credit: {coupon_code}")
            return response

        except APIRequestException as e:
            logger.exception(f"Failed to grant coupon credit: {e}")
            raise

    def grant_credit_to_users(
        self,
        credit_amount: float,
        credit_type: CreditType,
        user_list: list[str],
        description: str | None = None,
        expires_in_days: int | None = None,
    ) -> dict[str, Any]:
        """Grant credit to multiple users (legacy compatibility method).

        Args:
            credit_amount: Amount of credit to grant
            credit_type: Type of credit
            user_list: List of user UUIDs to grant credit to
            description: Description of the credit
            expires_in_days: Expiration period in days

        Returns:
            Result dictionary with success_count
        """
        success_count = 0
        campaign_id = f"TEST-{credit_type.value}-{int(time.time())}"

        for user_uuid in user_list:
            if user_uuid == self.uuid:
                try:
                    # Convert days to months for expiration
                    expiration_months = None
                    if expires_in_days:
                        expiration_months = max(1, expires_in_days // 30)

                    self.grant_credit(
                        campaign_id=campaign_id,
                        amount=credit_amount,
                        credit_name=description or f"{credit_type.value} Credit",
                        expiration_months=expiration_months,
                    )
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to grant credit to {user_uuid}: {e}")

        return {"success_count": success_count}

    def grant_credit(
        self,
        campaign_id: str | None = None,
        amount: CreditAmount | None = None,
        credit_name: str | None = None,
        credit_type: CreditType | None = None,
        expiration_months: int | None = None,
        expiration_date_from: str | None = None,
        expiration_date_to: str | None = None,
    ) -> CreditData:
        """Grant credit to user through campaign (unified method).

        Args:
            campaign_id: Campaign ID for credit grant (auto-generated if not provided)
            amount: Credit amount to grant
            credit_name: Name/description of the credit
            credit_type: Type of credit (used to generate campaign ID if not provided)
            expiration_months: Expiration period in months
            expiration_date_from: Start date for credit validity
            expiration_date_to: End date for credit validity

        Returns:
            API response data

        Raises:
            ValidationException: If parameters are invalid
            APIRequestException: If credit grant fails
        """
        # Validate amount is provided
        if amount is None:
            msg = "Credit amount must be provided"
            raise ValidationException(msg)

        # Auto-generate campaign ID if not provided
        if not campaign_id:
            if credit_type:
                # Use credit type in campaign ID
                campaign_id = f"{credit_type.value}-{int(time.time())}"
            else:
                # Default campaign ID
                campaign_id = f"CAMPAIGN-{int(time.time())}"

        CreditCalculator.validate_credit_amount(amount)

        # Set defaults
        credit_name = credit_name or self.DEFAULT_CREDIT_NAME
        expiration_months = expiration_months or self.DEFAULT_EXPIRATION_MONTHS

        # Calculate dates if not provided
        if not expiration_date_from or not expiration_date_to:
            calc_from, calc_to = CreditCalculator.calculate_expiration_dates(
                expiration_months
            )
            expiration_date_from = expiration_date_from or calc_from
            expiration_date_to = expiration_date_to or calc_to

        # Create credit request
        credit_request = CreditRequest(
            campaign_id=campaign_id,
            amount=amount,
            credit_name=credit_name,
            expiration_period=expiration_months,
            expiration_date_from=expiration_date_from,
            expiration_date_to=expiration_date_to,
            uuid_list=[self.uuid],
        )

        # Add credit type to request data if provided
        if credit_type:
            setattr(credit_request, "credit_type", credit_type)

        logger.info(
            f"Granting credit: {amount} via campaign {campaign_id} "
            f"(expires: {expiration_date_from} to {expiration_date_to})"
        )

        try:
            response = self._api.grant_campaign_credit(
                campaign_id, credit_request, self.uuid
            )
            logger.info(f"Successfully granted credit: {amount}")
            return response

        except APIRequestException as e:
            logger.exception(f"Failed to grant credit: {e}")
            raise

    def get_credit_history(
        self,
        credit_type: CreditType | str = CreditType.FREE,
        page: int = 1,
        items_per_page: int = 100,
    ) -> tuple[CreditAmount, list[CreditHistory]]:
        """Get credit history for specified type.

        Args:
            credit_type: Type of credit (FREE or PAID)
            page: Page number for pagination
            items_per_page: Number of items per page

        Returns:
            Tuple of (total_amount, credit_history_list)

        Raises:
            ValidationException: If credit type is invalid
            APIRequestException: If inquiry fails
        """
        # Normalize credit type
        if isinstance(credit_type, str):
            try:
                credit_type = CreditType(credit_type.upper())
            except ValueError:
                msg = f"Invalid credit type: {credit_type}"
                raise ValidationException(msg)

        logger.info(f"Getting credit history: type={credit_type.value}, page={page}")

        try:
            response = self._api.get_credit_history(
                self.uuid, credit_type, page, items_per_page
            )

            # Parse response
            history_data = response.get("creditHistories", [])
            histories = [CreditHistory.from_api_response(item) for item in history_data]

            # Calculate total
            total_credit = CreditCalculator.calculate_total_from_history(histories)

            logger.info(
                f"Found {len(histories)} credit entries, total: {total_credit:,.2f}"
            )

            return total_credit, histories

        except APIRequestException as e:
            logger.exception(f"Failed to get credit history: {e}")
            raise

    def get_credit_balance(self, include_paid: bool = True) -> dict[str, CreditAmount]:
        """Get current credit balance.

        Args:
            include_paid: Whether to include paid credits

        Returns:
            Dictionary with credit balances by type

        Raises:
            APIRequestException: If inquiry fails
        """
        balance = {"free": 0.0, "paid": 0.0, "total": 0.0}

        try:
            # Get free credit balance
            free_total, _ = self.get_credit_history(CreditType.FREE)
            balance["free"] = free_total

            if include_paid:
                # Get paid credit balance
                paid_total, _ = self.get_credit_history(CreditType.PAID)
                balance["paid"] = paid_total

            balance["total"] = balance["free"] + balance["paid"]

            logger.info(
                f"Credit balance - Free: {balance['free']:,.2f}, "
                f"Paid: {balance['paid']:,.2f}, "
                f"Total: {balance['total']:,.2f}"
            )

            return balance

        except APIRequestException as e:
            logger.exception(f"Failed to get credit balance: {e}")
            raise

    def get_total_credit_balance(self, include_paid: bool = True) -> CreditAmount:
        """Get total credit balance as a single number.

        Args:
            include_paid: Whether to include paid credits

        Returns:
            Total credit amount
        """
        balance_dict = self.get_credit_balance(include_paid)
        total = 0.0

        for amount in balance_dict.values():
            if isinstance(amount, int | float):
                total += float(amount)

        return total

    def inquiry_credit_balance(self) -> dict[str, Any]:
        """Get credit balance in API response format (legacy method).

        Returns:
            API response with balance information
        """
        try:
            balance = self.get_total_credit_balance()
            return {
                "header": {
                    "isSuccessful": True,
                    "resultCode": 0,
                    "resultMessage": "Success",
                },
                "balance": balance,
            }
        except Exception as e:
            return {
                "header": {
                    "isSuccessful": False,
                    "resultCode": -1,
                    "resultMessage": str(e),
                },
                "balance": 0,
            }

    def bulk_grant_credit(
        self, campaign_ids: list[str], amount: CreditAmount, **kwargs: Any
    ) -> dict[str, CreditData | Exception]:
        """Grant credit to multiple campaigns.

        Args:
            campaign_ids: List of campaign IDs
            amount: Credit amount to grant to each
            **kwargs: Additional arguments for grant_credit

        Returns:
            Dictionary mapping campaign ID to result or exception
        """
        results: dict[str, CreditData | Exception] = {}

        for campaign_id in campaign_ids:
            try:
                result = self.grant_credit(campaign_id, amount, **kwargs)
                results[campaign_id] = result

            except Exception as e:
                logger.exception(f"Failed to grant credit to {campaign_id}: {e}")
                results[campaign_id] = e

        # Summary
        success_count = sum(1 for r in results.values() if not isinstance(r, Exception))
        logger.info(
            f"Bulk credit grant completed: "
            f"{success_count}/{len(campaign_ids)} successful"
        )

        return results

    def bulk_cancel_credit(
        self, campaign_ids: list[str], reason: str = "Bulk cancellation"
    ) -> dict[str, CreditData | Exception]:
        """Cancel credit for multiple campaigns.

        Args:
            campaign_ids: List of campaign IDs
            reason: Reason for cancellation

        Returns:
            Dictionary mapping campaign ID to result or exception
        """
        results: dict[str, CreditData | Exception] = {}

        for campaign_id in campaign_ids:
            try:
                result = self.cancel_credit(campaign_id, reason)
                results[campaign_id] = result

            except Exception as e:
                logger.exception(f"Failed to cancel credit for {campaign_id}: {e}")
                results[campaign_id] = e

        # Summary
        success_count = sum(1 for r in results.values() if not isinstance(r, Exception))
        logger.info(
            f"Bulk credit cancellation completed: "
            f"{success_count}/{len(campaign_ids)} successful"
        )

        return results

    def cancel_credit(self, campaign_id: str, reason: str = "test") -> dict[str, Any]:
        """Cancel a credit.

        Args:
            campaign_id: ID of the campaign to cancel
            reason: Reason for cancellation

        Returns:
            Cancellation result
        """
        endpoint = f"billing/admin/credits/{campaign_id}/cancel"
        params = {"reason": reason}

        try:
            return self._client.delete(endpoint, params=params)
        except APIRequestException as e:
            logger.exception("Failed to cancel credit: %s", e)
            raise


# Legacy compatibility alias
class Credit(CreditManager):
    """Legacy alias for CreditManager.

    .. deprecated:: 2.0
        Use CreditManager instead. This alias is kept for backward compatibility.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize with deprecation warning."""
        warnings.warn(
            "Credit class is deprecated. Use CreditManager instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
