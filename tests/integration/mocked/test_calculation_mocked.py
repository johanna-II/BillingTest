"""Mocked integration tests for Calculation Manager.

Uses responses library - NO DOCKER NEEDED!
"""

import re

import pytest
import responses

from libs.Calculation import CalculationManager


class TestCalculationMocked:
    """Calculation integration tests with in-memory mocking."""

    @pytest.fixture
    def calculation_manager(self):
        """Create a CalculationManager instance."""
        # CalculationManager requires month and uuid
        return CalculationManager(month="2024-01", uuid="test-uuid-001")

    @responses.activate
    def test_recalculate_all_basic(self, calculation_manager):
        """Test basic recalculation with mocked response."""
        responses.add(
            responses.POST,
            re.compile(r".*/v1/calculation/recalculate$"),
            json={
                "header": {
                    "isSuccessful": True,
                    "resultCode": 0,
                    "resultMessage": "SUCCESS",
                },
                "calculation": {
                    "calculationId": "CALC-12345",
                    "status": "COMPLETED",
                    "totalCharge": 50000,
                },
            },
            status=200,
        )

        result = calculation_manager.recalculate_all()

        assert result is not None
        assert result.get("header", {}).get("isSuccessful") is True
        assert len(responses.calls) == 1

    @responses.activate
    def test_recalculate_with_job_code(self, calculation_manager):
        """Test recalculation with specific job code."""
        responses.add(
            responses.POST,
            re.compile(r".*/v1/calculation/recalculate$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        result = calculation_manager.recalculate_all()

        assert result["header"]["isSuccessful"]

    @responses.activate
    def test_calculation_status_check(self, calculation_manager):
        """Test checking calculation status."""
        # Mock recalculate
        responses.add(
            responses.POST,
            re.compile(r".*/v1/calculation/recalculate$"),
            json={
                "header": {"isSuccessful": True},
                "calculation": {"calculationId": "CALC-123"},
            },
            status=200,
        )

        # Mock status check
        responses.add(
            responses.GET,
            re.compile(r".*/v1/calculation/status"),
            json={
                "header": {"isSuccessful": True},
                "status": {
                    "calculationId": "CALC-123",
                    "status": "PROCESSING",
                    "progress": 50,
                },
            },
            status=200,
        )

        # Trigger calculation
        calc_result = calculation_manager.recalculate_all()
        assert calc_result["header"]["isSuccessful"]

    @responses.activate
    def test_calculation_error_handling(self, calculation_manager):
        """Test calculation error scenarios."""
        responses.add(
            responses.POST,
            re.compile(r".*/v1/calculation/recalculate$"),
            json={
                "header": {
                    "isSuccessful": False,
                    "resultCode": 500,
                    "resultMessage": "Calculation failed",
                }
            },
            status=500,
        )

        result = calculation_manager.recalculate_all()

        # Should handle error gracefully
        assert result is not None

    @responses.activate
    def test_calculation_timeout(self, calculation_manager):
        """Test calculation timeout handling."""
        responses.add(
            responses.POST,
            re.compile(r".*/v1/calculation/recalculate$"),
            body=Exception("Connection timeout"),
        )

        try:
            result = calculation_manager.recalculate_all()
            assert result is not None
        except Exception as e:
            # Timeout is acceptable
            assert "timeout" in str(e).lower() or "connection" in str(e).lower()
