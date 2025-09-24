"""Unit tests for PaymentAPIClient."""

from unittest.mock import Mock, patch

import pytest

from libs.payment_api_client import PaymentAPIClient


class TestPaymentAPIClient:
    """Tests for PaymentAPIClient."""

    @pytest.fixture
    def mock_response(self):
        """Mock response object."""
        mock = Mock()
        mock.json.return_value = {"status": "success"}
        mock.status_code = 200
        return mock

    @pytest.fixture
    def client(self):
        """Create PaymentAPIClient instance."""
        return PaymentAPIClient("http://test.com")

    def test_get_statements_admin(self, client, mock_response):
        """Test get_statements_admin method."""
        with patch.object(client, "get", return_value={"statements": []}) as mock_get:
            result = client.get_statements_admin("2024-01", "test-uuid")

            assert result == {"statements": []}
            mock_get.assert_called_once_with(
                "billing/admin/statements",
                params={"uuid": "test-uuid", "month": "2024-01"},
            )

    def test_get_statements_console(self, client, mock_response):
        """Test get_statements_console method."""
        with patch.object(client, "get", return_value={"statements": []}) as mock_get:
            result = client.get_statements_console("2024-01", "test-uuid")

            assert result == {"statements": []}
            mock_get.assert_called_once_with(
                "billing/console/statements",
                params={"uuid": "test-uuid", "month": "2024-01"},
            )

    def test_change_status(self, client, mock_response):
        """Test change_status method."""
        with patch.object(
            client, "put", return_value={"status": "changed"}
        ) as mock_put:
            result = client.change_status("2024-01", "pg-123", "PAID")

            assert result == {"status": "changed"}
            mock_put.assert_called_once_with(
                "billing/payment/pg-123/status",
                json={"month": "2024-01", "status": "PAID"},
            )

    def test_cancel_payment(self, client, mock_response):
        """Test cancel_payment method."""
        with patch.object(
            client, "delete", return_value={"status": "cancelled"}
        ) as mock_delete:
            result = client.cancel_payment("2024-01", "pg-123")

            assert result == {"status": "cancelled"}
            mock_delete.assert_called_once_with(
                "billing/payment/pg-123", params={"month": "2024-01"}
            )

    def test_make_payment(self, client, mock_response):
        """Test make_payment method."""
        with patch.object(
            client, "post", return_value={"paymentId": "pay-123"}
        ) as mock_post:
            result = client.make_payment("2024-01", "pg-123", "test-uuid")

            assert result == {"paymentId": "pay-123"}
            mock_post.assert_called_once_with(
                "billing/payment/make",
                json={
                    "month": "2024-01",
                    "paymentGroupId": "pg-123",
                    "uuid": "test-uuid",
                },
            )

    def test_get_unpaid_statements(self, client, mock_response):
        """Test get_unpaid_statements method."""
        with patch.object(client, "get", return_value={"statements": []}) as mock_get:
            result = client.get_unpaid_statements("2024-01", "test-uuid")

            assert result == {"statements": []}
            mock_get.assert_called_once_with(
                "billing/unpaid", params={"month": "2024-01", "uuid": "test-uuid"}
            )

    def test_create_payment(self, client, mock_response):
        """Test create_payment method."""
        with patch.object(
            client, "post", return_value={"paymentId": "new-123"}
        ) as mock_post:
            result = client.create_payment("pg-123", 1000.0, "CREDIT_CARD")

            assert result == {"paymentId": "new-123"}
            mock_post.assert_called_once_with(
                "billing/payment",
                json={
                    "paymentGroupId": "pg-123",
                    "amount": 1000.0,
                    "paymentMethod": "CREDIT_CARD",
                },
            )

    def test_get_payment_details(self, client, mock_response):
        """Test get_payment_details method."""
        with patch.object(
            client, "get", return_value={"paymentId": "pay-123"}
        ) as mock_get:
            result = client.get_payment_details("pay-123")

            assert result == {"paymentId": "pay-123"}
            mock_get.assert_called_once_with("billing/payment/pay-123")

    def test_process_refund(self, client, mock_response):
        """Test process_refund method."""
        with patch.object(
            client, "post", return_value={"refundId": "ref-123"}
        ) as mock_post:
            result = client.process_refund("pay-123", 500.0, "Customer request")

            assert result == {"refundId": "ref-123"}
            mock_post.assert_called_once_with(
                "billing/refund",
                json={
                    "paymentId": "pay-123",
                    "amount": 500.0,
                    "reason": "Customer request",
                },
            )

    def test_get_payment_history(self, client, mock_response):
        """Test get_payment_history method."""
        with patch.object(
            client, "get", return_value={"payments": [{"id": "pay-1"}]}
        ) as mock_get:
            result = client.get_payment_history(
                payment_group_id="pg-123",
                start_date="2024-01-01",
                end_date="2024-01-31",
            )

            assert result == [{"id": "pay-1"}]
            mock_get.assert_called_once_with(
                "billing/payment/history",
                params={
                    "paymentGroupId": "pg-123",
                    "startDate": "2024-01-01",
                    "endDate": "2024-01-31",
                },
            )

    def test_retry_payment(self, client, mock_response):
        """Test retry_payment method."""
        with patch.object(
            client, "post", return_value={"status": "retried"}
        ) as mock_post:
            result = client.retry_payment("pay-123", 2)

            assert result == {"status": "retried"}
            mock_post.assert_called_once_with(
                "billing/payment/pay-123/retry", json={"retryCount": 2}
            )

    def test_batch_process_payments(self, client, mock_response):
        """Test batch_process_payments method."""
        with patch.object(client, "post", return_value={"processed": 3}) as mock_post:
            result = client.batch_process_payments(
                ["pay-1", "pay-2", "pay-3"], "process"
            )

            assert result == {"processed": 3}
            mock_post.assert_called_once_with(
                "billing/payment/batch",
                json={"paymentIds": ["pay-1", "pay-2", "pay-3"], "action": "process"},
            )
