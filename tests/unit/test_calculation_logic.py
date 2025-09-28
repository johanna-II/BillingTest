"""Unit tests for CalculationManager business logic."""

from unittest.mock import Mock, patch

import pytest

from libs.Calculation import CalculationManager


class TestCalculationLogic:
    """Unit tests for calculation business logic."""

    @pytest.fixture
    def calc_manager(self):
        """Create CalculationManager with mocked client."""
        mock_client = Mock()
        return CalculationManager(
            month="2024-01", uuid="test-uuid-123", client=mock_client
        )

    def test_initialization(self):
        """Test CalculationManager initialization."""
        manager = CalculationManager(month="2024-01", uuid="test-uuid")
        assert manager.month == "2024-01"
        assert manager.uuid == "test-uuid"
        assert manager._client is not None

    def test_recalculate_all_request_structure(self, calc_manager):
        """Test recalculation request data structure."""
        calc_manager._client.post.return_value = {"success": True}
        calc_manager._client.wait_for_completion.return_value = True

        result = calc_manager.recalculate_all(include_usage=True, timeout=60)

        # Verify API call
        calc_manager._client.post.assert_called_once_with(
            "billing/admin/calculations",
            json_data={
                "includeUsage": True,
                "month": "2024-01",
                "uuid": "test-uuid-123",
            },
        )
        assert result["success"] is True

    def test_recalculate_without_usage(self, calc_manager):
        """Test recalculation without usage data."""
        calc_manager._client.post.return_value = {"jobId": "123"}
        calc_manager._client.wait_for_completion.return_value = True

        calc_manager.recalculate_all(include_usage=False)

        call_args = calc_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]
        assert posted_data["includeUsage"] is False

    def test_wait_for_completion_parameters(self, calc_manager):
        """Test wait for completion with different parameters."""
        calc_manager._client.post.return_value = {"success": True}
        calc_manager._client.wait_for_completion.return_value = True

        calc_manager.recalculate_all(timeout=120)

        # Verify wait_for_completion was called with correct params
        calc_manager._client.wait_for_completion.assert_called_once_with(
            check_endpoint="billing/admin/progress?month=2024-01&uuid=test-uuid-123",
            status_field="status",
            success_value="COMPLETED",
            timeout=120,
            check_interval=3,
        )

    def test_wait_for_completion_timeout(self, calc_manager):
        """Test handling of calculation timeout."""
        calc_manager._client.post.return_value = {"success": True}
        calc_manager._client.wait_for_completion.return_value = False

        # Should still return the response even if timeout
        result = calc_manager.recalculate_all(timeout=5)
        assert result["success"] is True

    def test_delete_resources_request(self, calc_manager):
        """Test delete resources request structure."""
        calc_manager._client.delete.return_value = {"deleted": True}

        result = calc_manager.delete_resources()

        calc_manager._client.delete.assert_called_once_with(
            "billing/admin/resources",
            params={"month": "2024-01"},
            headers={"uuid": "test-uuid-123"},
        )
        assert result["deleted"] is True

    def test_repr_string(self, calc_manager):
        """Test string representation."""
        repr_str = repr(calc_manager)
        assert "CalculationManager" in repr_str
        assert "2024-01" in repr_str
        assert "test-uuid-123" in repr_str

    def test_calculation_progress_endpoint_format(self, calc_manager):
        """Test progress endpoint URL formatting."""
        calc_manager._client.post.return_value = {"success": True}
        calc_manager._client.wait_for_completion.return_value = True

        # Test with different month formats
        calc_manager.month = "2025-12"
        calc_manager.uuid = "special-uuid"

        calc_manager.recalculate_all()

        wait_call = calc_manager._client.wait_for_completion.call_args
        endpoint = wait_call[1]["check_endpoint"]
        assert "month=2025-12" in endpoint
        assert "uuid=special-uuid" in endpoint

    def test_custom_check_interval(self, calc_manager):
        """Test custom check interval for progress monitoring."""
        calc_manager._client.post.return_value = {"success": True}

        # Mock the _wait_for_calculation_completion method
        with patch.object(
            calc_manager, "_wait_for_calculation_completion"
        ) as mock_wait:
            mock_wait.return_value = True
            calc_manager.recalculate_all(timeout=60)

            # Verify it was called with default check_interval
            mock_wait.assert_called_once_with(60)
