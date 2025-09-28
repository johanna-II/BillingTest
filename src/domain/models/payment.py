"""Payment domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class PaymentStatus(Enum):
    """Payment lifecycle states."""

    DRAFT = "DRAFT"
    REGISTERED = "REGISTERED"
    READY = "READY"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


@dataclass(frozen=True)
class UnpaidAmount:
    """Represents unpaid amount from previous periods."""

    amount: Decimal
    overdue_days: int = 0
    overdue_rate: Decimal = Decimal("0.05")  # 5% default
    period: str = ""

    def __post_init__(self) -> None:
        """Validate unpaid amount."""
        if self.amount < 0:
            msg = "Unpaid amount cannot be negative"
            raise ValueError(msg)
        if self.overdue_days < 0:
            msg = "Overdue days cannot be negative"
            raise ValueError(msg)
        if self.overdue_rate < 0 or self.overdue_rate > 1:
            msg = "Overdue rate must be between 0 and 1"
            raise ValueError(msg)

    @property
    def is_overdue(self) -> bool:
        """Check if payment is overdue."""
        return self.overdue_days > 0

    @property
    def overdue_charge(self) -> Decimal:
        """Calculate overdue charge."""
        if not self.is_overdue:
            return Decimal(0)

        # Simple overdue calculation - could be more complex
        return self.amount * self.overdue_rate

    @property
    def total_with_charges(self) -> Decimal:
        """Get total amount including overdue charges."""
        return self.amount + self.overdue_charge


@dataclass
class Payment:
    """Represents a payment transaction."""

    id: str
    payment_group_id: str
    amount: Decimal
    status: PaymentStatus
    method: str = "CREDIT_CARD"
    transaction_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    paid_at: datetime | None = None
    cancelled_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate payment."""
        if self.amount <= 0:
            msg = "Payment amount must be positive"
            raise ValueError(msg)

    def can_transition_to(self, new_status: PaymentStatus) -> bool:
        """Check if status transition is valid."""
        valid_transitions = {
            PaymentStatus.DRAFT: [PaymentStatus.REGISTERED, PaymentStatus.CANCELLED],
            PaymentStatus.REGISTERED: [PaymentStatus.READY, PaymentStatus.CANCELLED],
            PaymentStatus.READY: [PaymentStatus.PAID, PaymentStatus.CANCELLED],
            PaymentStatus.PAID: [PaymentStatus.REFUNDED],
            PaymentStatus.CANCELLED: [],
            PaymentStatus.REFUNDED: [],
        }

        return new_status in valid_transitions.get(self.status, [])

    def transition_to(self, new_status: PaymentStatus) -> Payment:
        """Transition to new status if valid."""
        if not self.can_transition_to(new_status):
            msg = f"Invalid transition from {self.status} to {new_status}"
            raise ValueError(msg)

        # Create new instance with updated status
        kwargs: dict[str, Any] = {
            "id": self.id,
            "payment_group_id": self.payment_group_id,
            "amount": self.amount,
            "status": new_status,
            "method": self.method,
            "transaction_id": self.transaction_id,
            "created_at": self.created_at,
            "paid_at": self.paid_at,
            "cancelled_at": self.cancelled_at,
        }

        # Update timestamps based on transition
        if new_status == PaymentStatus.PAID:
            kwargs["paid_at"] = datetime.now()
        elif new_status == PaymentStatus.CANCELLED:
            kwargs["cancelled_at"] = datetime.now()

        return Payment(
            id=str(kwargs["id"]),
            payment_group_id=str(kwargs["payment_group_id"]),
            amount=Decimal(kwargs["amount"]),
            status=PaymentStatus(kwargs["status"]),
            method=str(kwargs.get("method", "CREDIT_CARD")),
            transaction_id=(
                kwargs.get("transaction_id") if kwargs.get("transaction_id") is not None else None
            ),
            created_at=kwargs.get("created_at", datetime.now()),
            paid_at=kwargs.get("paid_at"),
            cancelled_at=kwargs.get("cancelled_at"),
        )

    @property
    def is_complete(self) -> bool:
        """Check if payment is in a final state."""
        return self.status in [
            PaymentStatus.PAID,
            PaymentStatus.CANCELLED,
            PaymentStatus.REFUNDED,
        ]
