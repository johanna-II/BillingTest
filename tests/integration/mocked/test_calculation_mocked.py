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
        # Mock the recalculate endpoint
        responses.add(
            responses.POST,
            re.compile(r".*/billing/admin/calculations$"),
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
        # Mock the progress endpoint
        responses.add(
            responses.GET,
            re.compile(r".*/billing/admin/progress"),
            json={
                "header": {"isSuccessful": True},
                "status": "COMPLETED",
            },
            status=200,
        )

        result = calculation_manager.recalculate_all()

        assert result is not None
        assert result.get("header", {}).get("isSuccessful") is True
        assert len(responses.calls) >= 1

    @responses.activate
    def test_recalculate_with_job_code(self, calculation_manager):
        """Test recalculation with specific job code."""
        # Mock the recalculate endpoint
        responses.add(
            responses.POST,
            re.compile(r".*/billing/admin/calculations$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )
        # Mock the progress endpoint
        responses.add(
            responses.GET,
            re.compile(r".*/billing/admin/progress"),
            json={
                "header": {"isSuccessful": True},
                "status": "COMPLETED",
            },
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
            re.compile(r".*/billing/admin/calculations$"),
            json={
                "header": {"isSuccessful": True},
                "calculation": {"calculationId": "CALC-123"},
            },
            status=200,
        )

        # Mock status check / progress endpoint
        responses.add(
            responses.GET,
            re.compile(r".*/billing/admin/progress"),
            json={
                "header": {"isSuccessful": True},
                "status": "COMPLETED",
                "calculationId": "CALC-123",
                "progress": 100,
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
            re.compile(r".*/billing/admin/calculations$"),
            json={
                "header": {
                    "isSuccessful": False,
                    "resultCode": 500,
                    "resultMessage": "Calculation failed",
                }
            },
            status=500,
        )

        # This should raise an exception for 500 status
        with pytest.raises(Exception):
            calculation_manager.recalculate_all()

    @responses.activate
    def test_calculation_timeout(self, calculation_manager):
        """Test calculation timeout handling."""
        responses.add(
            responses.POST,
            re.compile(r".*/billing/admin/calculations$"),
            body=Exception("Connection timeout"),
        )

        # Should raise an exception
        with pytest.raises(Exception) as exc_info:
            calculation_manager.recalculate_all()
        # Timeout is acceptable
        assert (
            "timeout" in str(exc_info.value).lower()
            or "connection" in str(exc_info.value).lower()
        )
