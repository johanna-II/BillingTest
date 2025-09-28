"""Credit domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class CreditType(Enum):
    """Types of credits in the system."""

    FREE = "FREE"
    PAID = "PAID"
    REFUND = "REFUND"


class CreditPriority(Enum):
    """Credit usage priority (lower number = higher priority)."""

    EXPIRING_SOON = 1
    FREE = 2
    REFUND = 3
    PAID = 4


@dataclass(frozen=True)
class Credit:
    """Represents a credit in the billing system.

    This is an immutable value object that encapsulates credit behavior.
    """

    id: str
    type: CreditType
    amount: Decimal
    balance: Decimal
    expires_at: datetime
    created_at: datetime
    campaign_id: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        """Validate credit invariants."""
        if self.amount <= 0:
            msg = "Credit amount must be positive"
            raise ValueError(msg)
        if self.balance < 0:
            msg = "Credit balance cannot be negative"
            raise ValueError(msg)
        if self.balance > self.amount:
            msg = "Credit balance cannot exceed original amount"
            raise ValueError(msg)
        if self.expires_at <= self.created_at:
            msg = "Expiration date must be after creation date"
            raise ValueError(msg)

    @property
    def is_expired(self) -> bool:
        """Check if credit has expired."""
        return datetime.now() > self.expires_at

    @property
    def is_available(self) -> bool:
        """Check if credit can be used."""
        return not self.is_expired and self.balance > 0

    @property
    def days_until_expiry(self) -> int:
        """Calculate days until expiration."""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.now()
        return delta.days

    @property
    def priority(self) -> CreditPriority:
        """Determine credit priority for usage order."""
        if self.days_until_expiry <= 7:
            return CreditPriority.EXPIRING_SOON
        if self.type == CreditType.FREE:
            return CreditPriority.FREE
        if self.type == CreditType.REFUND:
            return CreditPriority.REFUND
        return CreditPriority.PAID

    def can_use(self, amount: Decimal) -> bool:
        """Check if credit can cover the specified amount."""
        return self.is_available and self.balance >= amount

    def use(self, amount: Decimal) -> Credit:
        """Use credit and return new instance with updated balance."""
        if not self.can_use(amount):
            msg = f"Cannot use {amount} from credit with balance {self.balance}"
            raise ValueError(msg)

        return Credit(
            id=self.id,
            type=self.type,
            amount=self.amount,
            balance=self.balance - amount,
            expires_at=self.expires_at,
            created_at=self.created_at,
            campaign_id=self.campaign_id,
            description=self.description,
        )


@dataclass
class CreditApplication:
    """Result of applying credits to an amount."""

    original_amount: Decimal
    credits_used: list[tuple[Credit, Decimal]] = field(default_factory=list)
    remaining_amount: Decimal = field(init=False)
    total_credits_applied: Decimal = field(init=False)

    def __post_init__(self) -> None:
        """Calculate derived fields."""
        self.total_credits_applied = Decimal(
            sum(amount for _, amount in self.credits_used)
        )
        self.remaining_amount = max(
            Decimal(0), self.original_amount - self.total_credits_applied
        )

    @property
    def is_fully_covered(self) -> bool:
        """Check if amount is fully covered by credits."""
        return self.remaining_amount == 0

    def add_credit_usage(self, credit: Credit, amount: Decimal) -> None:
        """Add a credit usage to the application."""
        if amount > credit.balance:
            msg = "Cannot use more than credit balance"
            raise ValueError(msg)

        self.credits_used.append((credit, amount))
        self.__post_init__()  # Recalculate derived fields
