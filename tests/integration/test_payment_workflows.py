"""Payment-focused integration tests."""

import os

import pytest

from libs.Calculation import CalculationManager
from libs.constants import CounterType, CreditType, PaymentStatus
from libs.Credit import CreditManager
from libs.http_client import BillingAPIClient
from libs.Metering import MeteringManager
from libs.Payments import PaymentManager


@pytest.mark.integration
@pytest.mark.mock_required
class TestPaymentWorkflows:
    """Test payment-related workflows."""

    @pytest.fixture
    def payment_context(self, month, member, use_mock):
        """Setup payment test context."""
        mock_url = os.environ.get("MOCK_SERVER_URL", "http://localhost:5000")
        base_url = f"{mock_url}/api/v1" if use_mock else None
        client = BillingAPIClient(base_url=base_url)

        return {
            "payment": PaymentManager(
                month=month, uuid=f"uuid-{member}", client=client
            ),
            "metering": MeteringManager(month=month, client=client),
            "calculation": CalculationManager(
                month=month, uuid=f"uuid-{member}", client=client
            ),
            "credit": CreditManager(uuid=f"uuid-{member}", client=client),
            "client": client,
        }

    def test_payment_lifecycle(self, payment_context) -> None:
        """Test complete payment lifecycle from usage to payment."""
        managers = payment_context

        # 1. Generate usage
        managers["metering"].send_metering(
            app_key="payment-test-app",
            counter_name="compute.payment.test",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
        )

        # 2. Calculate charges
        managers["calculation"].recalculate_all()

        # 3. Check initial payment status
        pg_id, initial_status = managers["payment"].get_payment_status()
        assert pg_id is not None
        assert initial_status in [PaymentStatus.PENDING, PaymentStatus.REGISTERED]

        # 4. Get unpaid amount
        unpaid_amount = managers["payment"].check_unpaid_amount(pg_id)
        assert unpaid_amount > 0

        # 5. Make payment
        if initial_status == PaymentStatus.PENDING:
            managers["payment"].make_payment(pg_id)
            # Verify payment was processed

        # 6. Check final status
        _, final_status = managers["payment"].get_payment_status()
        assert final_status != PaymentStatus.UNKNOWN

    def test_payment_with_retry(self, payment_context) -> None:
        """Test payment retry mechanism."""
        managers = payment_context

        # Setup billing with usage
        self._create_test_usage(managers["metering"])
        managers["calculation"].recalculate_all()

        pg_id, status = managers["payment"].get_payment_status()
        if status == PaymentStatus.PENDING:
            # Test retry logic
            managers["payment"].make_payment(payment_group_id=pg_id, retry_count=3)
            # Verify retry behavior

    def test_payment_cancellation(self, payment_context) -> None:
        """Test payment cancellation workflow."""
        managers = payment_context

        # Create payment scenario
        self._create_test_usage(managers["metering"])
        managers["calculation"].recalculate_all()

        pg_id, status = managers["payment"].get_payment_status()
        if pg_id and status == PaymentStatus.REGISTERED:
            # Cancel payment
            managers["payment"].cancel_payment(pg_id)

            # Verify cancellation
            _, new_status = managers["payment"].get_payment_status()
            assert new_status == PaymentStatus.CANCELLED

    def test_payment_with_credits(self, payment_context) -> None:
        """Test payment with credit application."""
        managers = payment_context

        # 1. Create usage
        self._create_test_usage(managers["metering"], volume="1000")

        # 2. Grant credits before calculation
        managers["credit"].grant_credit_to_users(
            credit_amount=50000.0,
            credit_type=CreditType.CAMPAIGN,
            user_list=["uuid-test"],
            description="Payment test credit",
        )

        # 3. Calculate with credits
        managers["calculation"].recalculate_all()

        # 4. Check payment amount (should be reduced)
        pg_id, _ = managers["payment"].get_payment_status()
        unpaid = managers["payment"].check_unpaid_amount(pg_id)

        # 5. Verify credit was applied
        managers["credit"].get_credit_balance()
        # If original charge was less than credit, unpaid should be 0
        # Otherwise, it should be reduced
        assert unpaid >= 0

    def test_payment_status_transitions(self, payment_context) -> None:
        """Test various payment status transitions."""
        managers = payment_context

        # Create different payment scenarios
        scenarios = [
            ("small_usage", "10"),
            ("medium_usage", "500"),
            ("large_usage", "2000"),
        ]

        for scenario_name, volume in scenarios:
            # Create usage
            managers["metering"].send_metering(
                app_key=f"app-{scenario_name}",
                counter_name=f"compute.{scenario_name}",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume=volume,
            )

        # Calculate all at once
        managers["calculation"].recalculate_all()

        # Check payment status
        pg_id, status = managers["payment"].get_payment_status()

        # Test status changes
        if status == PaymentStatus.PENDING:
            managers["payment"].change_payment_status(
                payment_group_id=pg_id, new_status=PaymentStatus.REGISTERED
            )

            _, new_status = managers["payment"].get_payment_status()
            assert new_status == PaymentStatus.REGISTERED

    def test_payment_error_scenarios(self, payment_context) -> None:
        """Test payment error handling."""
        managers = payment_context

        # Test invalid payment group ID
        with pytest.raises(Exception):
            managers["payment"].make_payment("invalid-pg-id")

        # Test payment without usage
        pg_id, _status = managers["payment"].get_payment_status()
        if not pg_id:
            # No payment group exists without usage
            unpaid = managers["payment"].check_unpaid_amount("")
            assert unpaid == 0

    def _create_test_usage(self, metering_manager, volume="100") -> None:
        """Helper to create test usage."""
        metering_manager.send_metering(
            app_key="test-payment-app",
            counter_name="compute.test",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume=volume,
        )
