"""Repository interfaces for domain entities.

These are abstract interfaces that define the contract for data access.
Concrete implementations will be in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from src.domain.models import (
    Adjustment,
    AdjustmentTarget,
    AdjustmentType,
    Contract,
    Credit,
    CreditType,
    MeteringData,
    Payment,
    PaymentStatus,
)

__all__ = [
    "AdjustmentRepository",
    "AdjustmentTarget",
    "AdjustmentType",
    "ContractRepository",
    "CreditRepository",
    "MeteringRepository",
    "PaymentRepository",
]


class MeteringRepository(ABC):
    """Repository interface for metering data."""

    @abstractmethod
    def find_by_user_and_period(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> list[MeteringData]:
        """Find all metering data for a user within a period."""

    @abstractmethod
    def save(self, meter: MeteringData) -> MeteringData:
        """Save metering data."""

    @abstractmethod
    def find_by_app_key(
        self, app_key: str, start_date: datetime, end_date: datetime
    ) -> list[MeteringData]:
        """Find metering data by app key."""


class AdjustmentRepository(ABC):
    """Repository interface for adjustments."""

    @abstractmethod
    def find_by_billing_group(
        self, billing_group_id: str, _effective_date: datetime
    ) -> list[Adjustment]:
        """Find adjustments for a billing group."""

    @abstractmethod
    def find_by_project(
        self, project_id: str, effective_date: datetime
    ) -> list[Adjustment]:
        """Find adjustments for a project."""

    @abstractmethod
    def save(self, adjustment: Adjustment) -> Adjustment:
        """Save an adjustment."""

    @abstractmethod
    def delete(self, adjustment_id: str) -> bool:
        """Delete an adjustment."""


class CreditRepository(ABC):
    """Repository interface for credits."""

    @abstractmethod
    def find_by_user(self, user_id: str) -> list[Credit]:
        """Find all credits for a user."""

    @abstractmethod
    def find_by_type(self, user_id: str, credit_type: CreditType) -> list[Credit]:
        """Find credits by type for a user."""

    @abstractmethod
    def save(self, credit: Credit) -> Credit:
        """Save a credit."""

    @abstractmethod
    def update_balance(self, credit_id: str, new_balance: Decimal) -> Credit:
        """Update credit balance after usage."""


class ContractRepository(ABC):
    """Repository interface for contracts."""

    @abstractmethod
    def find_active_contract(
        self, billing_group_id: str, as_of_date: datetime
    ) -> Contract | None:
        """Find active contract for a billing group."""

    @abstractmethod
    def find_by_id(self, contract_id: str) -> Contract | None:
        """Find contract by ID."""

    @abstractmethod
    def save(self, contract: Contract) -> Contract:
        """Save a contract."""


class PaymentRepository(ABC):
    """Repository interface for payments."""

    @abstractmethod
    def find_unpaid_by_user(self, user_id: str, before_date: datetime) -> list[Payment]:
        """Find unpaid payments before a certain date."""

    @abstractmethod
    def find_by_status(self, user_id: str, status: PaymentStatus) -> list[Payment]:
        """Find payments by status."""

    @abstractmethod
    def save(self, payment: Payment) -> Payment:
        """Save a payment."""

    @abstractmethod
    def update_status(self, payment_id: str, new_status: PaymentStatus) -> Payment:
        """Update payment status."""
