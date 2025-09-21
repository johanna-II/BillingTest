"""Credit management for billing system."""

import contextlib
import logging
from typing import TYPE_CHECKING, Any

from config import url

from .constants import CreditType
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient

if TYPE_CHECKING:
    from .types import CreditData

logger = logging.getLogger(__name__)


class CreditManager:
    """Manages credit operations including granting, inquiry, and cancellation."""

    def __init__(self, uuid: str) -> None:
        """Initialize credit manager.

        Args:
            uuid: User UUID for credit operations
        """
        self.uuid = uuid
        self._client = BillingAPIClient(url.BASE_BILLING_URL)

    def __repr__(self) -> str:
        return f"CreditManager(uuid={self.uuid})"

    def grant_coupon_credit(self, coupon_code: str) -> dict[str, Any]:
        """Grant coupon-based credit to user.

        Args:
            coupon_code: Code of the coupon to apply

        Returns:
            API response data

        Raises:
            APIRequestException: If credit grant fails
        """
        headers = {"Accept": "application/json;charset=UTF-8", "uuid": self.uuid}

        endpoint = f"billing/coupons/{coupon_code}"

        logger.info("Granting coupon credit with code: %s", coupon_code)

        try:
            response = self._client.post(endpoint, headers=headers)
            logger.info("Successfully granted coupon credit: %s", coupon_code)
            return response
        except APIRequestException as e:
            logger.exception("Failed to grant coupon credit: %s", e)
            raise

    def grant_direct_credit(
        self,
        campaign_id: str,
        amount: int,
        credit_name: str = "QA billing test",
        expiration_period: int = 1,
        expiration_date_from: str | None = None,
        expiration_date_to: str | None = None,
    ) -> dict[str, Any]:
        """Grant direct credit to user through campaign.

        Args:
            campaign_id: Campaign ID for credit grant
            amount: Credit amount to grant
            credit_name: Name/description of the credit
            expiration_period: Expiration period in months
            expiration_date_from: Start date for credit validity
            expiration_date_to: End date for credit validity

        Returns:
            API response data

        Raises:
            ValidationException: If amount is invalid
            APIRequestException: If credit grant fails
        """
        if amount <= 0:
            msg = f"Credit amount must be positive: {amount}"
            raise ValidationException(msg)

        headers = {"Accept": "application/json;charset=UTF-8", "uuid": self.uuid}

        credit_data: CreditData = {
            "creditName": credit_name,
            "credit": amount,
            "expirationDateFrom": expiration_date_from,
            "expirationDateTo": expiration_date_to,
            "expirationPeriod": expiration_period,
            "creditPayTargetData": self.uuid,
            "emailList": [],
            "uuidList": [self.uuid],
        }

        endpoint = f"billing/admin/campaign/{campaign_id}/credits"

        logger.info("Granting direct credit: {amount} via campaign %s", campaign_id)

        try:
            response = self._client.post(
                endpoint, headers=headers, json_data=credit_data
            )
            logger.info("Successfully granted direct credit: %s", amount)
            return response
        except APIRequestException as e:
            logger.exception("Failed to grant direct credit: %s", e)
            raise

    def grant_paid_credit(
        self,
        campaign_id: str,
        amount: int,
        credit_name: str = "test",
        expiration_date_from: str = "2021-03-01",
        expiration_date_to: str = "2022-03-01",
        expiration_period: int = 1,
    ) -> dict[str, Any]:
        """Grant paid credit to user.

        Args:
            campaign_id: Campaign ID for paid credit
            amount: Credit amount to grant
            credit_name: Name of the credit
            expiration_date_from: Start date for credit validity
            expiration_date_to: End date for credit validity
            expiration_period: Expiration period

        Returns:
            API response data

        Raises:
            APIRequestException: If credit grant fails
        """
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "Content-Type": "application/json",
            "uuid": self.uuid,
        }

        credit_data = {
            "credit": amount,
            "creditName": credit_name,
            "expirationDateFrom": expiration_date_from,
            "expirationDateTo": expiration_date_to,
            "expirationPeriod": expiration_period,
            "uuidList": [self.uuid],
        }

        endpoint = f"billing/admin/campaign/{campaign_id}/credits"

        logger.info("Granting paid credit: {amount} via campaign %s", campaign_id)

        try:
            response = self._client.post(
                endpoint, headers=headers, json_data=credit_data
            )
            logger.info("Successfully granted paid credit: %s", amount)
            return response
        except APIRequestException as e:
            logger.exception("Failed to grant paid credit: %s", e)
            raise

    def get_credit_history(
        self,
        credit_type: CreditType | str,
        page: int = 1,
        items_per_page: int = 100,
    ) -> int:
        """Get credit history for specified type.

        Args:
            credit_type: Type of credit (FREE or PAID)
            page: Page number for pagination
            items_per_page: Number of items per page

        Returns:
            Total credit amount

        Raises:
            ValidationException: If credit type is invalid
            APIRequestException: If inquiry fails
        """
        # Normalize credit type
        credit_type_str = (
            credit_type.value if isinstance(credit_type, CreditType) else credit_type
        )

        if credit_type_str not in [t.value for t in CreditType]:
            msg = f"Invalid credit type: {credit_type_str}"
            raise ValidationException(msg)

        params = {
            "balancePriceTypeCode": credit_type_str,
            "page": page,
            "itemsPerPage": items_per_page,
        }

        headers = {"Accept": "application/json;charset=UTF-8", "uuid": self.uuid}

        endpoint = "billing/credits/history"

        logger.info("Retrieving %s credit history", credit_type_str)

        try:
            response = self._client.get(endpoint, headers=headers, params=params)
            total_amount = response.get("totalCreditAmt", 0)
            logger.info("Total {credit_type_str} credit amount: %s", total_amount)
            return total_amount
        except APIRequestException as e:
            logger.exception("Failed to get credit history: %s", e)
            raise

    def get_remaining_credit(self) -> tuple[int, int]:
        """Get remaining credit balance.

        Returns:
            Tuple of (remaining_balance, total_credit_history)

        Raises:
            APIRequestException: If inquiry fails
        """
        headers = {"Accept": "application/json;charset=UTF-8", "uuid": self.uuid}

        endpoint = "billing/v5.0/credits"

        logger.info("Retrieving remaining credit balance")

        try:
            response = self._client.get(endpoint, headers=headers)

            # Get credit history
            free_history = self.get_credit_history(CreditType.FREE)
            paid_history = self.get_credit_history(CreditType.PAID)
            total_history = free_history + paid_history

            # Parse remaining credits
            total_remaining = response.get("stats", {}).get("totalAmount", 0)

            # Log credit breakdown if available
            rest_credits = response.get("stats", {}).get(
                "restCreditsByBalancePriceTypeCode", []
            )
            for credit_info in rest_credits:
                credit_type = credit_info.get("balancePriceTypeCode")
                rest_amount = credit_info.get("restAmount", 0)
                logger.info("{credit_type} remaining credit: %s", rest_amount)

            logger.info("Total remaining credit: {total_remaining}, Total history: %s", total_history
            )
            

            return total_remaining, total_history

        except APIRequestException as e:
            logger.exception("Failed to get remaining credit: %s", e)
            raise

    def cancel_credit(
        self, campaign_ids: str | list[str], reason: str = "test"
    ) -> dict[str, list[str]]:
        """Cancel credit for specified campaigns.

        Args:
            campaign_ids: Single campaign ID or list of IDs
            reason: Reason for cancellation

        Returns:
            Dictionary with successful and failed cancellations

        Raises:
            APIRequestException: If any cancellation fails critically
        """
        # Normalize to list
        if isinstance(campaign_ids, str):
            campaign_ids = [campaign_ids]

        headers = {"Accept": "application/json;charset=UTF-8"}

        successful = []
        failed = []

        for campaign_id in campaign_ids:
            endpoint = f"billing/admin/campaign/{campaign_id}/credits"
            params = {"reason": reason}

            logger.info("Cancelling credit for campaign: %s", campaign_id)

            try:
                self._client.delete(endpoint, headers=headers, params=params)
                successful.append(campaign_id)
                logger.info("Successfully cancelled credit for campaign: %s", campaign_id
                )
            except APIRequestException as e:
                failed.append(campaign_id)
                logger.exception("Failed to cancel credit for campaign {campaign_id}: %s", e)

        return {"successful": successful, "failed": failed}


# Backward compatibility wrapper
class Credit:
    """Legacy wrapper for backward compatibility."""

    def __init__(self) -> None:
        self._couponcode = ""
        self._uuid = ""
        self._headers = ""
        self._campaign_id = []
        self._give_campaign_id = []
        self._paid_campaign_id = []
        self._manager = None

    def __repr__(self) -> str:
        return (
            f"Credit(couponCode: {self.couponcode}, "
            f"uuid: {self.uuid}, couponId: {self.campaign_id}, "
            f"giveCouponId: {self.give_campaign_id}, paidCampaignId: {self.paid_campaign_id}"
        )

    @property
    def couponcode(self):
        return self._couponcode

    @couponcode.setter
    def couponcode(self, couponcode) -> None:
        self._couponcode = couponcode

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, uuid) -> None:
        self._uuid = uuid
        self._manager = CreditManager(uuid) if uuid else None

    @property
    def campaign_id(self):
        return self._campaign_id

    @campaign_id.setter
    def campaign_id(self, campaign_id) -> None:
        self._campaign_id = campaign_id

    @property
    def give_campaign_id(self):
        return self._give_campaign_id

    @give_campaign_id.setter
    def give_campaign_id(self, give_campaign_id) -> None:
        self._give_campaign_id = give_campaign_id

    @property
    def paid_campaign_id(self):
        return self._paid_campaign_id

    @paid_campaign_id.setter
    def paid_campaign_id(self, paid_campaign_id) -> None:
        self._paid_campaign_id = paid_campaign_id

    def give_credit(self, couponCode, *args) -> None:
        """Legacy method for granting credit."""
        if not self._manager:
            return

        try:
            if args:
                # Direct credit grant
                self._manager.grant_direct_credit(couponCode, args[0])
            else:
                # Coupon credit grant
                self._manager.grant_coupon_credit(couponCode)
        except Exception:
            pass

    def give_paid_credit(self, **kwargs) -> None:
        """Legacy method for granting paid credit."""
        if not self._manager:
            return

        campaign_id = kwargs.get("campaignId")
        credit_amount = kwargs.get("creditAmount")

        with contextlib.suppress(Exception):
            self._manager.grant_paid_credit(campaign_id, credit_amount)

    def inquiry_credit(self, *args):
        """Legacy method for credit inquiry."""
        if not self._manager:
            return 0

        try:
            return self._manager.get_credit_history(args[0])
        except Exception:
            return 0

    def inquiry_rest_credit(self):
        """Legacy method for remaining credit inquiry."""
        if not self._manager:
            return "", ""

        try:
            remaining, total_history = self._manager.get_remaining_credit()

            if remaining > 0:
                pass
            else:
                pass

            return remaining, total_history
        except Exception:
            return "", ""

    def cancel_credit(self) -> None:
        """Legacy method for credit cancellation."""
        if not self._manager:
            return

        all_campaigns = self.campaign_id + self.give_campaign_id + self.paid_campaign_id

        if not all_campaigns:
            return

        try:
            result = self._manager.cancel_credit(all_campaigns)

            for _campaign_id in result["successful"]:
                pass

            for _campaign_id in result["failed"]:
                pass
        except Exception:
            pass
