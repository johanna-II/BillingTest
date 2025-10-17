"""Mocked integration tests for Credit Manager.

Uses responses library - NO DOCKER NEEDED!
"""

import re

import pytest
import responses

from libs.constants import CreditType
from libs.Credit import CreditManager


class TestCreditMocked:
    """Credit integration tests with in-memory mocking."""

    @pytest.fixture
    def credit_manager(self):
        """Create a CreditManager instance."""
        # CreditManager requires uuid parameter
        return CreditManager(uuid="test-uuid-001")

    @responses.activate
    def test_grant_credit_basic(self, credit_manager):
        """Test basic credit grant with mocked response."""
        responses.add(
            responses.POST,
            re.compile(r".*/v1/credit/grant$"),
            json={
                "header": {
                    "isSuccessful": True,
                    "resultCode": 0,
                    "resultMessage": "SUCCESS",
                },
                "credit": {
                    "creditId": "CRD-12345",
                    "amount": 10000,
                    "creditType": "CAMPAIGN",
                },
            },
            status=200,
        )

        result = credit_manager.grant_credit(
            campaign_id="TEST-CAMPAIGN-001",
            credit_name="Test Credit",
            amount=10000,
            credit_type=CreditType.CAMPAIGN,
        )

        assert result is not None
        assert result.get("header", {}).get("isSuccessful") is True
        assert len(responses.calls) == 1

    @responses.activate
    def test_grant_multiple_credit_types(self, credit_manager):
        """Test granting different credit types."""
        responses.add(
            responses.POST,
            re.compile(r".*/v1/credit/grant$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        # Campaign credit
        campaign_result = credit_manager.grant_credit(
            campaign_id="CAMPAIGN-001",
            credit_name="Campaign Credit",
            amount=5000,
            credit_type=CreditType.CAMPAIGN,
        )
        assert campaign_result["header"]["isSuccessful"]

        # Refund credit
        refund_result = credit_manager.grant_credit(
            campaign_id="REFUND-001",
            credit_name="Refund Credit",
            amount=3000,
            credit_type=CreditType.REFUND,
        )
        assert refund_result["header"]["isSuccessful"]

        assert len(responses.calls) == 2

    @responses.activate
    def test_get_credit_balance(self, credit_manager):
        """Test getting credit balance."""
        responses.add(
            responses.GET,
            re.compile(r".*/v1/credit/balance$"),
            json={
                "header": {"isSuccessful": True},
                "balance": {
                    "totalBalance": 15000,
                    "availableBalance": 12000,
                    "usedBalance": 3000,
                },
            },
            status=200,
        )

        result = credit_manager.get_total_credit_balance()

        assert result is not None
        assert len(responses.calls) == 1

    @responses.activate
    def test_grant_credit_with_expiry(self, credit_manager):
        """Test credit with expiration date."""
        responses.add(
            responses.POST,
            re.compile(r".*/v1/credit/grant$"),
            json={
                "header": {"isSuccessful": True},
                "credit": {"creditId": "CRD-EXP-001", "expiryDate": "2024-12-31"},
            },
            status=200,
        )

        result = credit_manager.grant_credit(
            campaign_id="EXP-CAMPAIGN",
            credit_name="Expiring Credit",
            amount=20000,
            credit_type=CreditType.CAMPAIGN,
        )

        assert result["header"]["isSuccessful"]

    @responses.activate
    def test_credit_error_handling(self, credit_manager):
        """Test credit error scenarios."""
        responses.add(
            responses.POST,
            re.compile(r".*/v1/credit/grant$"),
            json={
                "header": {
                    "isSuccessful": False,
                    "resultCode": 400,
                    "resultMessage": "Invalid credit amount",
                }
            },
            status=400,
        )

        result = credit_manager.grant_credit(
            campaign_id="ERROR-TEST",
            credit_name="Error Test",
            amount=-1000,  # Negative amount
            credit_type=CreditType.CAMPAIGN,
        )

        # Should handle error gracefully
        assert result is not None

    @responses.activate
    def test_bulk_credit_operations(self, credit_manager):
        """Test multiple credit operations."""
        responses.add(
            responses.POST,
            re.compile(r".*/v1/credit/grant$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        credits = [
            ("BULK-001", "Credit 1", 1000),
            ("BULK-002", "Credit 2", 2000),
            ("BULK-003", "Credit 3", 3000),
        ]

        for campaign_id, name, amount in credits:
            result = credit_manager.grant_credit(
                campaign_id=campaign_id,
                credit_name=name,
                amount=amount,
                credit_type=CreditType.CAMPAIGN,
            )
            assert result["header"]["isSuccessful"]

        assert len(responses.calls) == 3
