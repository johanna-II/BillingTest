"""Payment State Machine for managing payment status transitions."""

from typing import Callable, Dict, List, Set

from .constants import PaymentStatus
from .exceptions import ValidationException


class PaymentStateMachine:
    """Manages payment status transitions and validation.

    This class encapsulates the business logic for valid payment state transitions,
    making it easier to test and maintain separately from the PaymentManager.
    """

    # Define valid transitions
    TRANSITIONS: Dict[PaymentStatus, List[PaymentStatus]] = {
        PaymentStatus.PENDING: [PaymentStatus.REGISTERED],
        PaymentStatus.REGISTERED: [PaymentStatus.PAID, PaymentStatus.CANCELLED],
        PaymentStatus.PAID: [],  # Final state
        PaymentStatus.CANCELLED: [],  # Final state
        PaymentStatus.FAILED: [],  # Final state
        PaymentStatus.UNKNOWN: [PaymentStatus.PENDING],  # Can transition to pending
    }

    # Final states that cannot transition
    FINAL_STATES: Set[PaymentStatus] = {
        PaymentStatus.PAID,
        PaymentStatus.CANCELLED,
        PaymentStatus.FAILED,
    }

    # States that require payment action
    PAYABLE_STATES: Set[PaymentStatus] = {
        PaymentStatus.PENDING,
        PaymentStatus.REGISTERED,
    }

    @classmethod
    def can_transition(cls, from_status: PaymentStatus, to_status: PaymentStatus) -> bool:
        """Check if a transition from one status to another is valid.

        Args:
            from_status: Current payment status
            to_status: Target payment status

        Returns:
            True if transition is valid, False otherwise
        """
        return to_status in cls.TRANSITIONS.get(from_status, [])

    @classmethod
    def validate_transition(cls, from_status: PaymentStatus, to_status: PaymentStatus) -> None:
        """Validate a status transition, raising exception if invalid.

        Args:
            from_status: Current payment status
            to_status: Target payment status

        Raises:
            ValidationException: If transition is not valid
        """
        if not cls.can_transition(from_status, to_status):
            raise ValidationException(
                f"Invalid payment status transition: {from_status} -> {to_status}"
            )

    @classmethod
    def get_next_states(cls, current_status: PaymentStatus) -> List[PaymentStatus]:
        """Get list of valid next states from current status.

        Args:
            current_status: Current payment status

        Returns:
            List of valid next statuses
        """
        return cls.TRANSITIONS.get(current_status, [])

    @classmethod
    def is_final_state(cls, status: PaymentStatus) -> bool:
        """Check if a status is a final state.

        Args:
            status: Payment status to check

        Returns:
            True if status is final (no further transitions possible)
        """
        return status in cls.FINAL_STATES

    @classmethod
    def is_payable_state(cls, status: PaymentStatus) -> bool:
        """Check if a payment can be made in this state.

        Args:
            status: Payment status to check

        Returns:
            True if payment action is valid in this state
        """
        return status in cls.PAYABLE_STATES

    @classmethod
    def is_cancellable_state(cls, status: PaymentStatus) -> bool:
        """Check if a payment can be cancelled in this state.

        Args:
            status: Payment status to check

        Returns:
            True if cancellation is valid in this state
        """
        return status == PaymentStatus.REGISTERED

    @classmethod
    def get_transition_path(
        cls, from_status: PaymentStatus, to_status: PaymentStatus
    ) -> List[PaymentStatus]:
        """Get the path of transitions needed to go from one status to another.

        Args:
            from_status: Starting payment status
            to_status: Target payment status

        Returns:
            List of statuses representing the transition path, or empty list if no path exists
        """
        if from_status == to_status:
            return [from_status]

        # Simple BFS to find path
        queue = [(from_status, [from_status])]
        visited = {from_status}

        while queue:
            current, path = queue.pop(0)

            for next_status in cls.get_next_states(current):
                if next_status == to_status:
                    return path + [next_status]

                if next_status not in visited:
                    visited.add(next_status)
                    queue.append((next_status, path + [next_status]))

        return []  # No path exists

    @classmethod
    def validate_payment_action(cls, current_status: PaymentStatus, action: str) -> None:
        """Validate if a payment action is valid for current status.

        Args:
            current_status: Current payment status
            action: Action to perform ('pay', 'cancel', 'register')

        Raises:
            ValidationException: If action is not valid for current status
        """
        action_validations: Dict[str, Callable[[PaymentStatus], bool]] = {
            "pay": cls.is_payable_state,
            "cancel": cls.is_cancellable_state,
            "register": lambda s: s == PaymentStatus.PENDING,
        }

        validator = action_validations.get(action)
        if not validator:
            raise ValidationException(f"Unknown payment action: {action}")

        if not validator(current_status):
            raise ValidationException(f"Action '{action}' is not valid for status {current_status}")
