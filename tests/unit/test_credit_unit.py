"""Unit tests for Credit module with mocking."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from libs.Credit import CreditManager, CreditAPIClient, CreditRequest, CreditHistory
from libs.constants import CreditType
from libs.exceptions import APIRequestException, ValidationException


class TestCreditAPIClient:
    """Unit tests for CreditAPIClient class"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.credit_api = CreditAPIClient(self.mock_client)
        yield
    
    def test_grant_coupon_success(self):
        """Test successful coupon grant"""
        mock_response = {
            "credit": 1000,
            "creditName": "Test Coupon",
            "expirationDate": "2024-12-31"
        }
        self.mock_client.post.return_value = mock_response
        
        result = self.credit_api.grant_coupon("COUPON-123", "test-uuid")
        
        assert result == mock_response
        self.mock_client.post.assert_called_once_with(
            "billing/coupons/COUPON-123", 
            headers={"Accept": "application/json;charset=UTF-8", "uuid": "test-uuid"}
        )
    
    def test_grant_campaign_credit_success(self):
        """Test successful campaign credit grant"""
        mock_response = {
            "grantedCount": 1,
            "totalCredit": 1000
        }
        self.mock_client.post.return_value = mock_response
        
        credit_request = CreditRequest(
            campaign_id="CAMPAIGN-123",
            amount=1000,
            uuid_list=["test-uuid"]
        )
        
        result = self.credit_api.grant_campaign_credit(
            campaign_id="CAMPAIGN-123",
            credit_request=credit_request,
            uuid="test-uuid"
        )
        
        assert result == mock_response
    
    def test_get_credit_history_with_pagination(self):
        """Test credit history retrieval with pagination"""
        mock_response = {
            "creditHistories": [{"amount": 1000}],
            "totalCount": 10
        }
        self.mock_client.get.return_value = mock_response
        
        result = self.credit_api.get_credit_history(
            uuid="test-uuid",
            credit_type=CreditType.PAID,
            page=2,
            items_per_page=50
        )
        
        assert result == mock_response
        self.mock_client.get.assert_called_once_with(
            "billing/credits/history",
            headers={"Accept": "application/json;charset=UTF-8"},
            params={"uuid": "test-uuid", "creditType": "PAID", "page": 2, "itemsPerPage": 50}
        )
    
    def test_cancel_credit_success(self):
        """Test successful credit cancellation"""
        mock_response = {"status": "CANCELLED"}
        self.mock_client.delete.return_value = mock_response
        
        result = self.credit_api.cancel_credit("CAMPAIGN-123", reason="Test reason")
        
        assert result == mock_response
        self.mock_client.delete.assert_called_once_with(
            "billing/admin/campaign/CAMPAIGN-123/credits",
            headers={"Accept": "application/json;charset=UTF-8", "Content-Type": "application/json"},
            params={"reason": "Test reason"}
        )
    
    def test_get_credit_history_success(self):
        """Test successful credit history retrieval"""
        mock_response = {
            "creditHistories": [
                {
                    "creditHistoryId": "CH-001",
                    "creditType": "FREE",
                    "amount": 1000,
                    "balance": 800,
                    "transactionDate": "2024-01-15",
                    "description": "Credit granted"
                }
            ],
            "totalCount": 1
        }
        self.mock_client.get.return_value = mock_response
        
        result = self.credit_api.get_credit_history("uuid-123", credit_type=CreditType.FREE)
        
        assert result == mock_response
        self.mock_client.get.assert_called_once_with(
            "billing/credits/history",
            headers={"Accept": "application/json;charset=UTF-8"},
            params={"uuid": "uuid-123", "creditType": "FREE", "page": 1, "itemsPerPage": 100}
        )
    
    def test_cancel_credit_default_reason(self):
        """Test credit cancellation with default reason"""
        mock_response = {"status": "CANCELLED"}
        self.mock_client.delete.return_value = mock_response
        
        result = self.credit_api.cancel_credit("CAMPAIGN-123")
        
        assert result == mock_response
        self.mock_client.delete.assert_called_once_with(
            "billing/admin/campaign/CAMPAIGN-123/credits",
            headers={"Accept": "application/json;charset=UTF-8", "Content-Type": "application/json"},
            params={"reason": "test"}
        )


class TestCreditRequest:
    """Unit tests for CreditRequest dataclass"""
    
    def test_credit_request_creation_with_defaults(self):
        """Test creating CreditRequest with default values"""
        request = CreditRequest(
            campaign_id="CAMP-123",
            amount=1000
        )
        
        assert request.campaign_id == "CAMP-123"
        assert request.amount == 1000
        assert request.credit_name == "Test Credit"
        assert request.expiration_period == 1
        assert request.expiration_date_from == datetime.now().strftime("%Y-%m-%d")
        assert request.uuid_list == []
        assert request.email_list == []
    
    def test_credit_request_creation_with_custom_values(self):
        """Test creating CreditRequest with custom values"""
        request = CreditRequest(
            campaign_id="CAMP-456",
            amount=5000,
            credit_name="Custom Credit",
            expiration_period=2,
            expiration_date_from="2024-01-01",
            expiration_date_to="2025-12-31",
            uuid_list=["uuid1", "uuid2"],
            email_list=["test@example.com"]
        )
        
        assert request.campaign_id == "CAMP-456"
        assert request.amount == 5000
        assert request.credit_name == "Custom Credit"
        assert request.expiration_period == 2
        assert request.expiration_date_from == "2024-01-01"
        assert request.expiration_date_to == "2025-12-31"
        assert len(request.uuid_list) == 2
        assert len(request.email_list) == 1
    
    def test_credit_request_invalid_amount(self):
        """Test CreditRequest with invalid amount"""
        with pytest.raises(ValidationException) as exc_info:
            CreditRequest(
                campaign_id="CAMP-123",
                amount=-1000  # Negative amount
            )
        
        assert "Credit amount must be positive" in str(exc_info.value)
    
    def test_credit_request_to_api_format(self):
        """Test converting CreditRequest to API format"""
        request = CreditRequest(
            campaign_id="CAMP-123",
            amount=1000.5,
            credit_name="Test Credit",
            uuid_list=["uuid1"]
        )
        
        api_format = request.to_api_format()
        
        assert api_format["credit"] == 1000  # Should be converted to int
        assert api_format["creditName"] == "Test Credit"
        assert api_format["expirationPeriod"] == 1
        assert api_format["uuidList"] == ["uuid1"]
        assert "expirationDateFrom" in api_format
        assert "expirationDateTo" in api_format


class TestCreditHistory:
    """Unit tests for CreditHistory dataclass"""
    
    def test_credit_history_from_api_response(self):
        """Test creating CreditHistory from API response"""
        api_data = {
            "creditType": "FREE",
            "amount": 1000.0,
            "balance": 800.0,
            "transactionDate": "2024-01-15T10:00:00Z",
            "description": "Credit granted",
            "campaignId": "CAMP-123"
        }
        
        history = CreditHistory.from_api_response(api_data)
        
        assert history.credit_type == CreditType.FREE
        assert history.amount == 1000.0
        assert history.balance == 800.0
        assert history.transaction_date == "2024-01-15T10:00:00Z"
        assert history.description == "Credit granted"
        assert history.campaign_id == "CAMP-123"
    
    def test_credit_history_from_api_response_missing_fields(self):
        """Test creating CreditHistory with missing optional fields"""
        api_data = {
            "creditType": "PAID",
            "amount": 500
            # Missing other fields
        }
        
        history = CreditHistory.from_api_response(api_data)
        
        assert history.credit_type == CreditType.PAID
        assert history.amount == 500.0
        assert history.balance == 0.0  # Default value
        assert history.transaction_date == ""  # Default value
        assert history.description == ""  # Default value
        assert history.campaign_id is None  # Default value


class TestCreditManagerBase:
    """Unit tests for CreditManager base functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.credit_manager = CreditManager(uuid="test-uuid-123", client=self.mock_client)
        self.mock_api_client = self.credit_manager._api
        yield
    
    def test_grant_credit_to_users_success(self):
        """Test granting credit to multiple users"""
        self.mock_api_client.grant_credit.return_value = {
            "grantedCount": 2,
            "totalCredit": 2000
        }
        
        result = self.credit_manager.grant_credit_to_users(
            campaign_id="CAMP-123",
            amount=1000,
            uuid_list=["uuid1", "uuid2"],
            credit_name="Test Credit"
        )
        
        assert result["grantedCount"] == 2
        assert result["totalCredit"] == 2000
        
        # Verify API call
        call_args = self.mock_api_client.grant_credit.call_args
        assert call_args[0][0] == "CAMP-123"
        credit_data = call_args[0][1]
        assert credit_data["credit"] == 1000
        assert credit_data["creditName"] == "Test Credit"
        assert credit_data["uuidList"] == ["uuid1", "uuid2"]
    
    def test_grant_credit_to_users_invalid_amount(self):
        """Test granting credit with invalid amount"""
        with pytest.raises(ValidationException) as exc_info:
            self.credit_manager.grant_credit_to_users(
                campaign_id="CAMP-123",
                amount=-1000,  # Negative amount
                uuid_list=["uuid1"]
            )
        
        assert "Amount must be positive" in str(exc_info.value)
    
    def test_grant_credit_to_users_empty_list(self):
        """Test granting credit with empty user list"""
        with pytest.raises(ValidationException) as exc_info:
            self.credit_manager.grant_credit_to_users(
                campaign_id="CAMP-123",
                amount=1000,
                uuid_list=[]  # Empty list
            )
        
        assert "At least one UUID must be provided" in str(exc_info.value)
    
    def test_use_coupon_success(self):
        """Test successful coupon usage"""
        self.mock_api_client.use_coupon.return_value = {
            "status": "SUCCESS",
            "appliedCredit": 1000
        }
        
        result = self.credit_manager.use_coupon("uuid-123", "COUPON-123")
        
        assert result["status"] == "SUCCESS"
        assert result["appliedCredit"] == 1000
        self.mock_api_client.use_coupon.assert_called_once_with("uuid-123", "COUPON-123")
    
    def test_cancel_credit_success(self):
        """Test successful credit cancellation"""
        self.mock_api_client.cancel_credit.return_value = {"status": "CANCELLED"}
        
        result = self.credit_manager.cancel_credit("CAMP-123", "uuid-123", "CH-123")
        
        assert result["status"] == "CANCELLED"
        self.mock_api_client.cancel_credit.assert_called_once_with("CAMP-123", "uuid-123", "CH-123")
    
    def test_get_credit_history_success(self):
        """Test retrieving credit history"""
        mock_histories = {
            "creditHistories": [
                {
                    "creditType": "FREE",
                    "amount": 1000,
                    "balance": 800,
                    "transactionDate": "2024-01-15",
                    "description": "Credit granted"
                }
            ]
        }
        self.mock_api_client.get_credit_histories.return_value = mock_histories
        
        histories = self.credit_manager.get_credit_history(
            uuid="uuid-123",
            credit_type=CreditType.FREE,
            page=1
        )
        
        assert len(histories) == 1
        assert isinstance(histories[0], CreditHistory)
        assert histories[0].amount == 1000
        assert histories[0].credit_type == CreditType.FREE
    
    def test_get_credit_balance_success(self):
        """Test retrieving credit balance"""
        mock_balance = {
            "freeCredit": 1000,
            "freeRemainCredit": 800,
            "paidCredit": 500,
            "paidRemainCredit": 400
        }
        self.mock_api_client.get_credit_balance.return_value = mock_balance
        
        result = self.credit_manager.get_credit_balance("uuid-123", "2024-01")
        
        assert result == mock_balance
        self.mock_api_client.get_credit_balance.assert_called_once_with("uuid-123", "2024-01")
    
    def test_calculate_total_credit(self):
        """Test calculating total credit from histories"""
        histories = [
            CreditHistory(
                credit_type=CreditType.FREE,
                amount=1000,
                balance=800,
                transaction_date="2024-01-01",
                description="Grant"
            ),
            CreditHistory(
                credit_type=CreditType.FREE,
                amount=-200,
                balance=600,
                transaction_date="2024-01-02",
                description="Usage"
            ),
            CreditHistory(
                credit_type=CreditType.PAID,
                amount=500,
                balance=500,
                transaction_date="2024-01-03",
                description="Paid credit"
            )
        ]
        
        total = self.credit_manager.calculate_total_credit(histories, CreditType.FREE)
        assert total == 800  # 1000 - 200
        
        total_paid = self.credit_manager.calculate_total_credit(histories, CreditType.PAID)
        assert total_paid == 500
        
        total_all = self.credit_manager.calculate_total_credit(histories)
        assert total_all == 1300  # 1000 - 200 + 500


class TestCreditManager:
    """Unit tests for main CreditManager class"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.credit_manager = CreditManager(uuid="test-uuid-123", client=self.mock_client)
        self.mock_api_client = self.credit_manager._api
        yield
    
    def test_credit_manager_inherits_base(self):
        """Test that CreditManager is properly initialized"""
        assert isinstance(self.credit_manager, CreditManager)
    
    def test_credit_manager_has_api_client(self):
        """Test that CreditManager has api_client"""
        assert hasattr(self.credit_manager, '_api_client')
    
    @patch('libs.Credit.logger')
    def test_credit_manager_logging(self, mock_logger):
        """Test that operations are logged"""
        self.mock_api_client.grant_credit.return_value = {"grantedCount": 1}
        
        self.credit_manager.grant_credit_to_users(
            campaign_id="CAMP-123",
            amount=1000,
            uuid_list=["uuid1"]
        )
        
        # Verify logging occurred
        assert mock_logger.info.called