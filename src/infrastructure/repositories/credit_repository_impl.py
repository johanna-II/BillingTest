"""Concrete implementation of CreditRepository using existing libs."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from libs.Credit import CreditManager
from libs.Credit import CreditType as LibCreditType
from libs.http_client import BillingAPIClient
from src.domain.models import Credit, CreditType
from src.domain.repositories import CreditRepository


class CreditRepositoryImpl(CreditRepository):
    """Implementation of CreditRepository using existing CreditManager."""

    def __init__(self, client: BillingAPIClient, user_id: str):
        """Initialize with API client and user ID."""
        self.credit_manager = CreditManager(uuid=user_id, client=client)
        self.user_id = user_id

    def find_by_user(self, user_id: str) -> list[Credit]:
        """Find all credits for a user."""
        if user_id != self.user_id:
            msg = "Repository initialized for different user"
            raise ValueError(msg)

        credit_list = []

        # Get credits of each type
        for credit_type in CreditType:
            lib_type = self._map_credit_type_to_lib(credit_type)
            try:
                _, history_items = self.credit_manager.get_credit_history(lib_type)

                for item in history_items:
                    credit = self._map_history_to_domain(item, credit_type)
                    if credit:
                        credit_list.append(credit)

            except Exception as e:
                # Log error but continue with other types
                print(f"Error fetching {credit_type} credits: {e}")

        return credit_list

    def find_by_type(self, user_id: str, credit_type: CreditType) -> list[Credit]:
        """Find credits by type for a user."""
        if user_id != self.user_id:
            msg = "Repository initialized for different user"
            raise ValueError(msg)

        lib_type = self._map_credit_type_to_lib(credit_type)
        _, history_items = self.credit_manager.get_credit_history(lib_type)

        credit_list = []
        for item in history_items:
            credit = self._map_history_to_domain(item, credit_type)
            if credit:
                credit_list.append(credit)

        return credit_list

    def save(self, credit: Credit) -> Credit:
        """Save a credit."""
        # Map domain credit to lib API call using the unified grant_credit method
        # Convert domain CreditType to lib CreditType
        lib_credit_type = self._domain_to_lib_credit_type(credit.type)
        self.credit_manager.grant_credit(
            campaign_id=credit.campaign_id or f"{credit.type.value}-{credit.id}",
            credit_name=f"{credit.type.value} Credit - {credit.id}",
            amount=float(credit.amount),
            credit_type=lib_credit_type,
        )

        # Return the credit as saved (lib doesn't return full credit object)
        return credit

    def update_balance(self, credit_id: str, new_balance: Decimal) -> Credit:
        """Update credit balance after usage."""
        # The existing lib doesn't support balance updates directly
        # In a real implementation, this would update the backend
        # For now, we'll return a credit with updated balance

        # Find the credit first
        all_credits = self.find_by_user(self.user_id)
        for credit in all_credits:
            if credit.id == credit_id:
                # Create new instance with updated balance
                return Credit(
                    id=credit.id,
                    type=credit.type,
                    amount=credit.amount,
                    balance=new_balance,
                    expires_at=credit.expires_at,
                    created_at=credit.created_at,
                    campaign_id=credit.campaign_id,
                    description=credit.description,
                )

        msg = f"Credit {credit_id} not found"
        raise ValueError(msg)

    def _map_credit_type_to_lib(self, credit_type: CreditType) -> LibCreditType:
        """Map domain credit type to lib credit type."""
        mapping = {
            CreditType.FREE: LibCreditType.FREE,
            CreditType.PAID: LibCreditType.PAID,
            CreditType.REFUND: LibCreditType.FREE,  # Lib doesn't have REFUND type
        }
        return mapping[credit_type]

    def _map_history_to_domain(
        self, history_item: Any, credit_type: CreditType
    ) -> Credit | None:
        """Map credit history item to domain model."""
        try:
            # Handle both dict and CreditHistory types
            if hasattr(history_item, "__dict__"):
                # CreditHistory object
                credit_id = (
                    getattr(history_item, "campaign_id", None)
                    or f"CREDIT-{datetime.now().timestamp()}"
                )
                amount = Decimal(str(getattr(history_item, "amount", 0)))
                balance = Decimal(str(getattr(history_item, "balance", amount)))
            else:
                # Dictionary format
                credit_id = history_item.get(
                    "id", f"CREDIT-{datetime.now().timestamp()}"
                )
                amount = Decimal(str(history_item.get("amount", 0)))
                balance = Decimal(str(history_item.get("balance", amount)))

            # Parse dates
            if hasattr(history_item, "__dict__"):
                created_str = getattr(
                    history_item, "transaction_date", datetime.now().isoformat()
                )
                expires_str = "2099-12-31"  # CreditHistory doesn't have expiry
            else:
                created_str = history_item.get("createdAt", datetime.now().isoformat())
                expires_str = history_item.get("expiresAt", "2099-12-31")

            created_at = datetime.fromisoformat(created_str)
            expires_at = datetime.fromisoformat(expires_str)

            return Credit(
                id=credit_id,
                type=credit_type,
                amount=amount,
                balance=balance,
                expires_at=expires_at,
                created_at=created_at,
                campaign_id=history_item.get("campaignId"),
                description=history_item.get("description", ""),
            )
        except Exception as e:
            print(f"Error mapping credit history item: {e}")
            return None

    def _domain_to_lib_credit_type(self, credit_type: CreditType) -> LibCreditType:
        """Convert domain CreditType to library CreditType."""
        mapping = {
            CreditType.FREE: LibCreditType.FREE,
            CreditType.PAID: LibCreditType.PAID,
            CreditType.REFUND: LibCreditType.FREE,  # Lib doesn't have REFUND type
        }
        return mapping.get(credit_type, LibCreditType.FREE)
