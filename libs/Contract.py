"""Contract management for billing system."""

import contextlib
import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from config import url

from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient

if TYPE_CHECKING:
    from .types import ContractData

logger = logging.getLogger(__name__)


class ContractManager:
    """Manages billing contracts for billing groups."""

    def __init__(self, month: str, billing_group_id: str) -> None:
        """Initialize contract manager.

        Args:
            month: Target month in YYYY-MM format
            billing_group_id: Billing group ID for contract operations

        Raises:
            ValidationException: If parameters are invalid
        """
        self._validate_month_format(month)
        self.month = month
        self.billing_group_id = billing_group_id
        self._client = BillingAPIClient(url.BASE_BILLING_URL)

    def __repr__(self) -> str:
        return f"ContractManager(month={self.month}, billing_group_id={self.billing_group_id})"

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

    def apply_contract(
        self,
        contract_id: str,
        name: str = "billing group default",
        is_default: bool = True,
    ) -> dict[str, Any]:
        """Apply contract to billing group.

        Args:
            contract_id: Contract ID to apply
            name: Name for the contract application
            is_default: Whether this is the default contract

        Returns:
            API response data

        Raises:
            APIRequestException: If contract application fails
        """
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        contract_data: ContractData = {
            "contractId": contract_id,
            "defaultYn": "Y" if is_default else "N",
            "monthFrom": self.month,
            "name": name,
        }

        endpoint = f"billing/admin/billing-groups/{self.billing_group_id}"

        logger.info("Applying contract {contract_id} to billing group {self.billing_group_id} from %s", self.month
        )

        try:
            response = self._client.put(
                endpoint, headers=headers, json_data=contract_data
            )
            logger.info("Successfully applied contract %s", contract_id)
            return response
        except APIRequestException as e:
            logger.exception("Failed to apply contract: %s", e)
            raise

    def delete_contract(self) -> dict[str, Any]:
        """Delete contract from billing group.

        Returns:
            API response data

        Raises:
            APIRequestException: If contract deletion fails
        """
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        endpoint = f"billing/admin/billing-groups/{self.billing_group_id}/contracts"

        logger.info("Deleting contract from billing group %s", self.billing_group_id)

        try:
            response = self._client.delete(endpoint, headers=headers)
            logger.info("Successfully deleted contract")
            return response
        except APIRequestException as e:
            logger.exception("Failed to delete contract: %s", e)
            raise

    def get_contract_details(self, contract_id: str) -> dict[str, Any]:
        """Get contract details.

        Args:
            contract_id: Contract ID to query

        Returns:
            Contract details including base fee

        Raises:
            APIRequestException: If query fails
        """
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        endpoint = f"billing/admin/contracts/{contract_id}"

        logger.info("Getting details for contract %s", contract_id)

        try:
            response = self._client.get(endpoint, headers=headers)

            contract_info = response.get("contract", {})
            base_fee = contract_info.get("baseFee", 0)

            logger.info("Contract {contract_id} base fee: %s", base_fee)

            return {
                "contract_id": contract_id,
                "base_fee": base_fee,
                "contract_info": contract_info,
            }
        except APIRequestException as e:
            logger.exception("Failed to get contract details: %s", e)
            raise

    def get_counter_price(self, contract_id: str, counter_name: str) -> dict[str, Any]:
        """Get price for a specific counter in the contract.

        Args:
            contract_id: Contract ID
            counter_name: Counter name to query price for

        Returns:
            Price information including original and discounted prices

        Raises:
            APIRequestException: If query fails
        """
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        params = {"counterNames": counter_name}

        endpoint = f"billing/admin/contracts/{contract_id}/products/prices"

        logger.info("Getting price for counter {counter_name} in contract %s", contract_id
        )

        # Retry logic for potential temporary failures
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self._client.get(endpoint, headers=headers, params=params)

                prices = response.get("prices", {})
                price = prices.get("price", 0)
                original_price = prices.get("originalPrice", 0)

                logger.info("Counter {counter_name} - Discounted: {price}, Original: %s", original_price
                )

                return {
                    "counter_name": counter_name,
                    "price": price,
                    "original_price": original_price,
                    "discount_amount": original_price - price,
                    "discount_rate": (
                        ((original_price - price) / original_price * 100)
                        if original_price > 0
                        else 0
                    ),
                }
            except APIRequestException as e:
                if attempt < max_retries - 1:
                    logger.warning("Attempt %s failed, retrying...", attempt + 1)
                    continue
                logger.exception("Failed to get counter price after {max_retries} attempts: %s", e
                )
                raise
        return None

    def get_multiple_counter_prices(
        self, contract_id: str, counter_names: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Get prices for multiple counters in the contract.

        Args:
            contract_id: Contract ID
            counter_names: List of counter names to query

        Returns:
            Dictionary mapping counter names to their price information
        """
        results = {}

        for counter_name in counter_names:
            try:
                price_info = self.get_counter_price(contract_id, counter_name)
                results[counter_name] = price_info
            except APIRequestException as e:
                logger.exception("Failed to get price for {counter_name}: %s", e)
                results[counter_name] = {"error": str(e)}

        return results


# Backward compatibility wrapper
class Contract:
    """Legacy wrapper for backward compatibility."""

    def __init__(self, month: str, bgId: str) -> None:
        self.month = month
        self.bgId = bgId
        self._contractId = ""
        self._counterName = ""
        self._manager = ContractManager(month, bgId)

    def __repr__(self) -> str:
        pass

    @property
    def contract_id(self):
        return self._contractId

    @contract_id.setter
    def contract_id(self, contractId) -> None:
        self._contractId = contractId
    
    # Backward compatibility alias
    @property
    def contractId(self):
        return self._contractId
    
    @contractId.setter
    def contractId(self, value) -> None:
        self._contractId = value

    @property
    def counter_name(self):
        return self._counterName

    @counter_name.setter
    def counter_name(self, counterName) -> None:
        self._counterName = counterName
    
    # Backward compatibility alias
    @property
    def counterName(self):
        return self._counterName
    
    @counterName.setter
    def counterName(self, value) -> None:
        self._counterName = value

    def apply_contract(self) -> None:
        """Legacy method for applying contract."""
        with contextlib.suppress(Exception):
            self._manager.apply_contract(self.contractId)

    def delete_contract(self) -> None:
        """Legacy method for deleting contract."""
        with contextlib.suppress(Exception):
            self._manager.delete_contract()

    def inquiry_contract(self) -> None:
        """Legacy method for querying contract."""
        with contextlib.suppress(Exception):
            self._manager.get_contract_details(self.contractId)

    def inquiry_priceby_counter_name(self):
        """Legacy method for querying counter price."""
        try:
            price_info = self._manager.get_counter_price(
                self.contractId, self.counterName
            )

            # Return in legacy format
            cntcont = defaultdict(set)
            cntcont["price"].add(price_info["price"])
            cntcont["originalPrice"].add(price_info["original_price"])
            return cntcont
        except Exception:
            return None
