"""Contract management for billing system."""

import logging
from typing import TYPE_CHECKING, Any

from config import url

from .contract_validator import ContractValidator
from .exceptions import APIRequestException
from .http_client import BillingAPIClient

if TYPE_CHECKING:
    from .billing_types import ContractData

logger = logging.getLogger(__name__)

# Common headers
JSON_HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


class ContractManager:
    """Manages billing contracts for billing groups."""

    def __init__(
        self,
        month: str,
        billing_group_id: str,
        client: BillingAPIClient | None = None,
    ) -> None:
        """Initialize contract manager.

        Args:
            month: Target month in YYYY-MM format
            billing_group_id: Billing group ID for contract operations
            client: Optional BillingAPIClient instance for dependency injection

        Raises:
            ValidationException: If parameters are invalid
        """
        ContractValidator.validate_month_format(month)
        ContractValidator.validate_billing_group_id(billing_group_id)
        self.month = month
        self.billing_group_id = billing_group_id
        self._client = client if client else BillingAPIClient(url.BASE_BILLING_URL)

    def __repr__(self) -> str:
        """Return string representation of ContractManager."""
        return f"ContractManager(month={self.month}, billing_group_id={self.billing_group_id})"

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
        # Validate contract ID
        ContractValidator.validate_contract_id(contract_id)

        headers = JSON_HEADERS

        contract_data: ContractData = {
            "contractId": contract_id,
            "defaultYn": "Y" if is_default else "N",
            "monthFrom": self.month,
            "name": ContractValidator.format_contract_name(name),
        }

        endpoint = f"billing/admin/billing-groups/{self.billing_group_id}"

        logger.info(
            "Applying contract {contract_id} to billing group {self.billing_group_id} from %s",
            self.month,
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
        headers = JSON_HEADERS

        endpoint = f"billing/admin/billing-groups/{self.billing_group_id}/contracts"

        logger.info("Deleting contract from a billing group")

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
        headers = JSON_HEADERS

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
        headers = JSON_HEADERS

        params = {"counterNames": counter_name}

        endpoint = f"billing/admin/contracts/{contract_id}/products/prices"

        logger.info(
            "Getting price for counter {counter_name} in contract %s", contract_id
        )

        # Retry logic for potential temporary failures
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self._client.get(endpoint, headers=headers, params=params)

                prices = response.get("prices", {})
                price = prices.get("price", 0)
                original_price = prices.get("originalPrice", 0)

                logger.info(
                    "Counter {counter_name} - Discounted: {price}, Original: %s",
                    original_price,
                )

                # Use ContractValidator for discount calculation
                discount_amount, discount_rate = ContractValidator.calculate_discount(
                    original_price, price
                )

                return {
                    "counter_name": counter_name,
                    "price": price,
                    "original_price": original_price,
                    "discount_amount": float(discount_amount),
                    "discount_rate": float(discount_rate),
                }
            except APIRequestException as e:
                if attempt < max_retries - 1:
                    logger.warning("Attempt %s failed, retrying...", attempt + 1)
                    continue
                logger.exception(
                    "Failed to get counter price after {max_retries} attempts: %s", e
                )
                raise
        # This should never be reached due to the raise above
        msg = "Unexpected code path in get_counter_price"
        raise RuntimeError(msg)

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
