"""Mocked integration tests for Adjustment Manager.

Uses responses library - NO DOCKER NEEDED!
"""

import re

import pytest
import responses

from libs.Adjustment import AdjustmentManager
from libs.constants import AdjustmentTarget, AdjustmentType


class TestAdjustmentMocked:
    """Adjustment integration tests with in-memory mocking."""

    @pytest.fixture
    def adjustment_manager(self):
        """Create an AdjustmentManager instance."""
        return AdjustmentManager(month="2024-01")

    @responses.activate
    def test_apply_adjustment_basic(self, adjustment_manager):
        """Test basic adjustment application."""
        responses.add(
            responses.POST,
            re.compile(r".*/billing/admin/projects/adjustments$"),
            json={
                "header": {
                    "isSuccessful": True,
                    "resultCode": 0,
                    "resultMessage": "SUCCESS",
                },
                "adjustment": {
                    "adjustmentId": "ADJ-12345",
                    "adjustmentType": "RATE_DISCOUNT",
                    "adjustmentAmount": 10.0,
                },
            },
            status=200,
        )

        result = adjustment_manager.apply_adjustment(
            adjustment_name="Test Discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=10.0,
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id="test-project-001",
        )

        assert result is not None
        assert result.get("header", {}).get("isSuccessful") is True
        assert len(responses.calls) == 1

    @responses.activate
    def test_different_adjustment_types(self, adjustment_manager):
        """Test different adjustment types."""
        # Mock for both project and billing group endpoints
        responses.add(
            responses.POST,
            re.compile(r".*/billing/admin/(projects|billing-groups)/adjustments$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        # Rate discount
        rate_result = adjustment_manager.apply_adjustment(
            adjustment_name="Rate Discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=15.0,
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id="proj-001",
        )
        assert rate_result["header"]["isSuccessful"]

        # Fixed discount
        fixed_result = adjustment_manager.apply_adjustment(
            adjustment_name="Fixed Discount",
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            adjustment_amount=5000,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-001",
        )
        assert fixed_result["header"]["isSuccessful"]

        assert len(responses.calls) == 2

    @responses.activate
    def test_adjustment_targets(self, adjustment_manager):
        """Test different adjustment targets."""
        # Mock for both project and billing group endpoints
        responses.add(
            responses.POST,
            re.compile(r".*/billing/admin/(projects|billing-groups)/adjustments$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        # Project-level adjustment
        project_result = adjustment_manager.apply_adjustment(
            adjustment_name="Project Discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=10.0,
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id="project-123",
        )
        assert project_result["header"]["isSuccessful"]

        # Billing group-level adjustment
        bg_result = adjustment_manager.apply_adjustment(
            adjustment_name="BG Discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=5.0,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-456",
        )
        assert bg_result["header"]["isSuccessful"]

        assert len(responses.calls) == 2

    @responses.activate
    def test_surcharge_adjustments(self, adjustment_manager):
        """Test surcharge (positive) adjustments."""
        # Mock for both project and billing group endpoints
        responses.add(
            responses.POST,
            re.compile(r".*/billing/admin/(projects|billing-groups)/adjustments$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        # Rate surcharge
        rate_surcharge = adjustment_manager.apply_adjustment(
            adjustment_name="Peak Hour Surcharge",
            adjustment_type=AdjustmentType.RATE_SURCHARGE,
            adjustment_amount=20.0,
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id="proj-peak",
        )
        assert rate_surcharge["header"]["isSuccessful"]

        # Fixed surcharge
        fixed_surcharge = adjustment_manager.apply_adjustment(
            adjustment_name="Service Fee",
            adjustment_type=AdjustmentType.FIXED_SURCHARGE,
            adjustment_amount=10000,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-fee",
        )
        assert fixed_surcharge["header"]["isSuccessful"]

        assert len(responses.calls) == 2

    @responses.activate
    def test_adjustment_with_description(self, adjustment_manager):
        """Test adjustment with detailed description."""
        # Mock for billing group endpoint
        responses.add(
            responses.POST,
            re.compile(r".*/billing/admin/billing-groups/adjustments$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        result = adjustment_manager.apply_adjustment(
            adjustment_name="Early Payment Discount",
            adjustment_description="Discount for paying before due date",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=3.0,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-early-pay",
        )

        assert result["header"]["isSuccessful"]

    def test_adjustment_error_handling(self, adjustment_manager):
        """Test adjustment error scenarios."""
        # Test validation error for > 100% rate discount
        # This should raise ValidationException before making API call
        with pytest.raises(Exception) as exc_info:
            adjustment_manager.apply_adjustment(
                adjustment_name="Invalid Adjustment",
                adjustment_type=AdjustmentType.RATE_DISCOUNT,
                adjustment_amount=150.0,  # > 100%
                adjustment_target=AdjustmentTarget.PROJECT,
                target_id="proj-invalid",
            )
        # Should be ValidationException
        assert "100%" in str(exc_info.value) or "ValidationException" in str(
            type(exc_info.value)
        )
