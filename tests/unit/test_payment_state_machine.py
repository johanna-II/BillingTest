"""Unit tests for PaymentStateMachine - pure state transition logic."""

import pytest

from libs.constants import PaymentStatus
from libs.exceptions import ValidationException
from libs.payment_state_machine import PaymentStateMachine


class TestPaymentStateMachine:
    """Unit tests for payment state machine logic."""

    def test_valid_transitions(self):
        """Test all valid state transitions."""
        # PENDING -> REGISTERED
        assert PaymentStateMachine.can_transition(PaymentStatus.PENDING, PaymentStatus.REGISTERED)

        # REGISTERED -> PAID
        assert PaymentStateMachine.can_transition(PaymentStatus.REGISTERED, PaymentStatus.PAID)

        # REGISTERED -> CANCELLED
        assert PaymentStateMachine.can_transition(PaymentStatus.REGISTERED, PaymentStatus.CANCELLED)

        # UNKNOWN -> PENDING (recovery case)
        assert PaymentStateMachine.can_transition(PaymentStatus.UNKNOWN, PaymentStatus.PENDING)

    def test_invalid_transitions(self):
        """Test invalid state transitions."""
        # Cannot go backwards
        assert not PaymentStateMachine.can_transition(PaymentStatus.PAID, PaymentStatus.PENDING)
        assert not PaymentStateMachine.can_transition(
            PaymentStatus.REGISTERED, PaymentStatus.PENDING
        )

        # Cannot skip states
        assert not PaymentStateMachine.can_transition(PaymentStatus.PENDING, PaymentStatus.PAID)

        # Cannot transition from final states
        assert not PaymentStateMachine.can_transition(PaymentStatus.PAID, PaymentStatus.CANCELLED)
        assert not PaymentStateMachine.can_transition(PaymentStatus.CANCELLED, PaymentStatus.PAID)
        assert not PaymentStateMachine.can_transition(PaymentStatus.FAILED, PaymentStatus.PENDING)

    def test_validate_transition_raises_on_invalid(self):
        """Test that validate_transition raises exception for invalid transitions."""
        with pytest.raises(ValidationException, match="Invalid payment status transition"):
            PaymentStateMachine.validate_transition(PaymentStatus.PENDING, PaymentStatus.PAID)

        with pytest.raises(ValidationException, match="Invalid payment status transition"):
            PaymentStateMachine.validate_transition(PaymentStatus.PAID, PaymentStatus.PENDING)

    def test_validate_transition_success_on_valid(self):
        """Test that validate_transition succeeds for valid transitions."""
        # Should not raise
        PaymentStateMachine.validate_transition(PaymentStatus.PENDING, PaymentStatus.REGISTERED)
        PaymentStateMachine.validate_transition(PaymentStatus.REGISTERED, PaymentStatus.PAID)

    def test_get_next_states(self):
        """Test getting valid next states."""
        # From PENDING
        next_states = PaymentStateMachine.get_next_states(PaymentStatus.PENDING)
        assert next_states == [PaymentStatus.REGISTERED]

        # From REGISTERED
        next_states = PaymentStateMachine.get_next_states(PaymentStatus.REGISTERED)
        assert set(next_states) == {PaymentStatus.PAID, PaymentStatus.CANCELLED}

        # From PAID (final state)
        next_states = PaymentStateMachine.get_next_states(PaymentStatus.PAID)
        assert next_states == []

        # From UNKNOWN
        next_states = PaymentStateMachine.get_next_states(PaymentStatus.UNKNOWN)
        assert next_states == [PaymentStatus.PENDING]

    def test_is_final_state(self):
        """Test final state detection."""
        # Final states
        assert PaymentStateMachine.is_final_state(PaymentStatus.PAID)
        assert PaymentStateMachine.is_final_state(PaymentStatus.CANCELLED)
        assert PaymentStateMachine.is_final_state(PaymentStatus.FAILED)

        # Non-final states
        assert not PaymentStateMachine.is_final_state(PaymentStatus.PENDING)
        assert not PaymentStateMachine.is_final_state(PaymentStatus.REGISTERED)
        assert not PaymentStateMachine.is_final_state(PaymentStatus.UNKNOWN)

    def test_is_payable_state(self):
        """Test payable state detection."""
        # Payable states
        assert PaymentStateMachine.is_payable_state(PaymentStatus.PENDING)
        assert PaymentStateMachine.is_payable_state(PaymentStatus.REGISTERED)

        # Non-payable states
        assert not PaymentStateMachine.is_payable_state(PaymentStatus.PAID)
        assert not PaymentStateMachine.is_payable_state(PaymentStatus.CANCELLED)
        assert not PaymentStateMachine.is_payable_state(PaymentStatus.FAILED)
        assert not PaymentStateMachine.is_payable_state(PaymentStatus.UNKNOWN)

    def test_is_cancellable_state(self):
        """Test cancellable state detection."""
        # Only REGISTERED can be cancelled
        assert PaymentStateMachine.is_cancellable_state(PaymentStatus.REGISTERED)

        # All others cannot be cancelled
        assert not PaymentStateMachine.is_cancellable_state(PaymentStatus.PENDING)
        assert not PaymentStateMachine.is_cancellable_state(PaymentStatus.PAID)
        assert not PaymentStateMachine.is_cancellable_state(PaymentStatus.CANCELLED)
        assert not PaymentStateMachine.is_cancellable_state(PaymentStatus.FAILED)
        assert not PaymentStateMachine.is_cancellable_state(PaymentStatus.UNKNOWN)

    def test_get_transition_path(self):
        """Test finding transition paths between states."""
        # Direct transition
        path = PaymentStateMachine.get_transition_path(
            PaymentStatus.PENDING, PaymentStatus.REGISTERED
        )
        assert path == [PaymentStatus.PENDING, PaymentStatus.REGISTERED]

        # Two-step transition
        path = PaymentStateMachine.get_transition_path(PaymentStatus.PENDING, PaymentStatus.PAID)
        assert path == [
            PaymentStatus.PENDING,
            PaymentStatus.REGISTERED,
            PaymentStatus.PAID,
        ]

        # Same state
        path = PaymentStateMachine.get_transition_path(PaymentStatus.PAID, PaymentStatus.PAID)
        assert path == [PaymentStatus.PAID]

        # No path exists
        path = PaymentStateMachine.get_transition_path(PaymentStatus.PAID, PaymentStatus.PENDING)
        assert path == []

        # From UNKNOWN to PAID
        path = PaymentStateMachine.get_transition_path(PaymentStatus.UNKNOWN, PaymentStatus.PAID)
        assert path == [
            PaymentStatus.UNKNOWN,
            PaymentStatus.PENDING,
            PaymentStatus.REGISTERED,
            PaymentStatus.PAID,
        ]

    def test_validate_payment_action(self):
        """Test payment action validation."""
        # Valid actions
        PaymentStateMachine.validate_payment_action(PaymentStatus.PENDING, "pay")
        PaymentStateMachine.validate_payment_action(PaymentStatus.REGISTERED, "pay")
        PaymentStateMachine.validate_payment_action(PaymentStatus.REGISTERED, "cancel")
        PaymentStateMachine.validate_payment_action(PaymentStatus.PENDING, "register")

        # Invalid actions
        with pytest.raises(ValidationException, match="not valid for status"):
            PaymentStateMachine.validate_payment_action(PaymentStatus.PAID, "pay")

        with pytest.raises(ValidationException, match="not valid for status"):
            PaymentStateMachine.validate_payment_action(PaymentStatus.PENDING, "cancel")

        with pytest.raises(ValidationException, match="not valid for status"):
            PaymentStateMachine.validate_payment_action(PaymentStatus.REGISTERED, "register")

        # Unknown action
        with pytest.raises(ValidationException, match="Unknown payment action"):
            PaymentStateMachine.validate_payment_action(PaymentStatus.PENDING, "unknown")

    def test_state_transition_consistency(self):
        """Test that state machine is internally consistent."""
        # All states in TRANSITIONS should be valid PaymentStatus values
        all_statuses = set(PaymentStatus)

        for from_status, to_statuses in PaymentStateMachine.TRANSITIONS.items():
            assert from_status in all_statuses
            for to_status in to_statuses:
                assert to_status in all_statuses

        # All final states should have no transitions
        for final_state in PaymentStateMachine.FINAL_STATES:
            assert PaymentStateMachine.get_next_states(final_state) == []

        # All payable states should not be final
        for payable_state in PaymentStateMachine.PAYABLE_STATES:
            assert not PaymentStateMachine.is_final_state(payable_state)
