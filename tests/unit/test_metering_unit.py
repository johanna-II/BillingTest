"""Unit tests for metering module."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from libs.Metering import MeteringManager, Metering
from libs.constants import CounterType
from libs.exceptions import ValidationException, APIRequestException


class TestMeteringManagerUnit:
    """Unit tests for MeteringManager class"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        with patch('libs.Metering.BillingAPIClient') as mock_client_class:
            self.mock_client = Mock()
            mock_client_class.return_value = self.mock_client
            self.metering = MeteringManager(month="2024-01")
            yield
    
    def test_init_success(self):
        """Test successful MeteringManager initialization"""
        assert self.metering.month == "2024-01"
        assert hasattr(self.metering, '_client')
        assert hasattr(self.metering, '_iaas_template')
    
    @patch('libs.Metering.BillingAPIClient')
    def test_init_invalid_month_format(self, mock_client_class):
        """Test initialization with invalid month format"""
        with pytest.raises(ValidationException) as exc_info:
            MeteringManager(month="2024-1")  # Invalid format
        
        assert "Invalid month format" in str(exc_info.value)
        assert "Expected YYYY-MM" in str(exc_info.value)
    
    def test_string_representation(self):
        """Test string representation of MeteringManager"""
        assert repr(self.metering) == "MeteringManager(month=2024-01)"
    
    def test_send_metering_success(self):
        """Test successful metering data submission"""
        mock_response = {
            "status": "SUCCESS",
            "processedCount": 1
        }
        self.mock_client.post.return_value = mock_response
        
        result = self.metering.send_metering(
            app_key="test-app-key",
            counter_name="compute.c2.c8m8",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
            resource_id="vm-123",
            resource_name="Test VM"
        )
        
        assert result == mock_response
        
        # Verify API call
        expected_data = {
            "meterList": [{
                "appKey": "test-app-key",
                "counterName": "compute.c2.c8m8",
                "counterType": "DELTA",
                "counterUnit": "HOURS",
                "counterVolume": "100",
                "parentResourceId": "test",
                "resourceId": "vm-123",
                "resourceName": "Test VM",
                "source": "qa.billing.test",
                "timestamp": "2024-01-01T13:00:00.000+09:00"
            }]
        }
        
        self.mock_client.post.assert_called_once_with(
            "billing/meters",
            json_data=expected_data
        )
    
    def test_send_metering_with_string_counter_type(self):
        """Test sending metering with string counter type"""
        self.mock_client.post.return_value = {"status": "SUCCESS"}
        
        result = self.metering.send_metering(
            app_key="test-app",
            counter_name="storage.volume",
            counter_type="GAUGE",  # String instead of enum
            counter_unit="GB",
            counter_volume="500"
        )
        
        assert result["status"] == "SUCCESS"
        
        # Verify counter type was correctly used
        call_args = self.mock_client.post.call_args
        meter_data = call_args[1]["json_data"]["meterList"][0]
        assert meter_data["counterType"] == "GAUGE"
    
    def test_send_metering_invalid_counter_type(self):
        """Test sending metering with invalid counter type"""
        with pytest.raises(ValidationException) as exc_info:
            self.metering.send_metering(
                app_key="test-app",
                counter_name="test.counter",
                counter_type="INVALID_TYPE",
                counter_unit="COUNT",
                counter_volume="10"
            )
        
        assert "Invalid counter type" in str(exc_info.value)
    
    def test_send_metering_api_error(self):
        """Test metering submission with API error"""
        self.mock_client.post.side_effect = APIRequestException("Metering failed")
        
        with pytest.raises(APIRequestException) as exc_info:
            self.metering.send_metering(
                app_key="test-app",
                counter_name="test.counter",
                counter_type=CounterType.DELTA,
                counter_unit="COUNT",
                counter_volume="10"
            )
        
        assert "Metering failed" in str(exc_info.value)
    
    def test_delete_metering_single_app_key(self):
        """Test deleting metering data for single app key"""
        self.metering.delete_metering("test-app-key")
        
        expected_params = {
            "appKey": "test-app-key",
            "from": "2024-01-01",
            "to": "2024-01-31"
        }
        
        self.mock_client.delete.assert_called_once_with(
            "billing/admin/meters",
            params=expected_params
        )
    
    def test_delete_metering_multiple_app_keys(self):
        """Test deleting metering data for multiple app keys"""
        app_keys = ["app-1", "app-2", "app-3"]
        
        result = self.metering.delete_metering(app_keys)
        
        assert result["deleted_count"] == 3
        assert self.mock_client.delete.call_count == 3
        
        # Verify each delete call
        for idx, app_key in enumerate(app_keys):
            expected_params = {
                "appKey": app_key,
                "from": "2024-01-01",
                "to": "2024-01-31"
            }
            actual_call = self.mock_client.delete.call_args_list[idx]
            assert actual_call[0][0] == "billing/admin/meters"
            assert actual_call[1]["params"] == expected_params
    
    def test_delete_metering_api_error(self):
        """Test delete metering with API error"""
        self.mock_client.delete.side_effect = APIRequestException("Delete failed")
        
        with pytest.raises(APIRequestException) as exc_info:
            self.metering.delete_metering("test-app")
        
        assert "Delete failed" in str(exc_info.value)
    
    @patch('libs.Metering.calendar.monthrange')
    def test_delete_metering_different_months(self, mock_monthrange):
        """Test delete metering for different months"""
        # Test February (non-leap year)
        mock_monthrange.return_value = (0, 28)
        metering_feb = MeteringManager(month="2023-02")
        metering_feb._client = self.mock_client
        
        metering_feb.delete_metering("test-app")
        
        expected_params = {
            "appKey": "test-app",
            "from": "2023-02-01",
            "to": "2023-02-28"
        }
        self.mock_client.delete.assert_called_with(
            "billing/admin/meters",
            params=expected_params
        )
    
    def test_send_batch_metering_success(self):
        """Test sending batch metering data"""
        metering_items = [
            {
                "counter_name": "compute.c2.c8m8",
                "counter_type": "DELTA",
                "counter_unit": "HOURS",
                "counter_volume": "100"
            },
            {
                "counter_name": "storage.volume",
                "counter_type": "GAUGE",
                "counter_unit": "GB",
                "counter_volume": "500"
            }
        ]
        
        self.mock_client.post.return_value = {"status": "SUCCESS"}
        
        result = self.metering.send_batch_metering("test-app", metering_items)
        
        assert len(result["results"]) == 2
        assert all(r["success"] for r in result["results"])
        assert self.mock_client.post.call_count == 2
    
    def test_send_batch_metering_partial_failure(self):
        """Test batch metering with partial failures"""
        metering_items = [
            {
                "counter_name": "compute.c2.c8m8",
                "counter_type": "DELTA",
                "counter_unit": "HOURS",
                "counter_volume": "100"
            },
            {
                "counter_name": "storage.volume",
                "counter_type": "GAUGE",
                "counter_unit": "GB",
                "counter_volume": "500"
            }
        ]
        
        # First call succeeds, second fails
        self.mock_client.post.side_effect = [
            {"status": "SUCCESS"},
            APIRequestException("Failed")
        ]
        
        result = self.metering.send_batch_metering("test-app", metering_items)
        
        assert len(result["results"]) == 2
        assert result["results"][0]["success"] is True
        assert result["results"][1]["success"] is False
        assert "Failed" in result["results"][1]["error"]
    
    def test_validate_month_format_valid(self):
        """Test month format validation with valid formats"""
        valid_months = ["2024-01", "2024-12", "2023-06", "2022-09"]
        
        for month in valid_months:
            # Should not raise exception
            MeteringManager._validate_month_format(month)
    
    def test_validate_month_format_invalid(self):
        """Test month format validation with invalid formats"""
        invalid_months = ["2024", "2024-1", "2024-13", "24-01", "2024/01", ""]
        
        for month in invalid_months:
            with pytest.raises(ValidationException):
                MeteringManager._validate_month_format(month)
    
    def test_create_default_template(self):
        """Test creation of default metering template"""
        template = MeteringManager._create_default_template()
        
        assert "meterList" in template
        assert len(template["meterList"]) == 1
        
        meter = template["meterList"][0]
        assert meter["source"] == "qa.billing.test"
        assert meter["parentResourceId"] == "test"
        assert meter["resourceId"] == "test"
        assert meter["resourceName"] == "test"


class TestMeteringLegacyWrapper:
    """Unit tests for legacy Metering wrapper"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        with patch('libs.Metering.MeteringManager') as mock_manager_class:
            self.mock_manager = Mock()
            mock_manager_class.return_value = self.mock_manager
            self.mock_manager._iaas_template = {"meterList": [{}]}
            self.metering = Metering(month="2024-01")
            yield
    
    def test_init_legacy(self):
        """Test legacy Metering initialization"""
        assert self.metering.month == "2024-01"
        assert hasattr(self.metering, '_manager')
        assert hasattr(self.metering, '_appkey')
        assert self.metering._appkey == ""
    
    def test_appkey_property_get(self):
        """Test getting appkey property"""
        self.metering._appkey = "test-app"
        assert self.metering.appkey == "test-app"
    
    def test_appkey_property_set(self):
        """Test setting appkey property"""
        self.metering.appkey = "new-app"
        assert self.metering._appkey == "new-app"
    
    def test_string_representation_legacy(self):
        """Test string representation of legacy Metering"""
        self.metering.appkey = "test-app"
        repr_str = repr(self.metering)
        assert "month: 2024-01" in repr_str
        assert "appkey: test-app" in repr_str
    
    def test_delete_metering_legacy_single_appkey(self):
        """Test legacy delete_metering with single appkey"""
        self.metering.appkey = "test-app"
        
        self.metering.delete_metering()
        
        self.mock_manager.delete_metering.assert_called_once_with(["test-app"])
    
    def test_delete_metering_legacy_list_appkey(self):
        """Test legacy delete_metering with list of appkeys"""
        self.metering.appkey = ["app1", "app2", "app3"]
        
        self.metering.delete_metering()
        
        self.mock_manager.delete_metering.assert_called_once_with(["app1", "app2", "app3"])
    
    def test_delete_metering_legacy_exception_suppressed(self):
        """Test legacy delete_metering suppresses exceptions"""
        self.metering.appkey = "test-app"
        self.mock_manager.delete_metering.side_effect = Exception("Test error")
        
        # Should not raise exception
        self.metering.delete_metering()
        
        self.mock_manager.delete_metering.assert_called_once()
    
    def test_send_iaas_metering_legacy(self):
        """Test legacy send_iaas_metering method"""
        self.metering.appkey = "test-app"
        
        kwargs = {
            "counter_name": "compute.c2.c8m8",
            "counter_type": "DELTA",
            "counter_unit": "HOURS",
            "counter_volume": "100"
        }
        
        self.metering.send_iaas_metering(**kwargs)
        
        self.mock_manager.send_metering.assert_called_once_with(
            app_key="test-app",
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="100"
        )
    
    def test_send_iaas_metering_legacy_exception_suppressed(self):
        """Test legacy send_iaas_metering suppresses exceptions"""
        self.metering.appkey = "test-app"
        self.mock_manager.send_metering.side_effect = Exception("Test error")
        
        # Should not raise exception
        self.metering.send_iaas_metering(
            counter_name="test",
            counter_type="DELTA",
            counter_unit="COUNT",
            counter_volume="1"
        )
        
        self.mock_manager.send_metering.assert_called_once()
    
    def test_send_iaas_metering_legacy_missing_params(self):
        """Test legacy send_iaas_metering with missing parameters"""
        self.metering.appkey = "test-app"
        
        # Missing all required parameters
        self.metering.send_iaas_metering()
        
        self.mock_manager.send_metering.assert_called_once_with(
            app_key="test-app",
            counter_name="",
            counter_type="",
            counter_unit="",
            counter_volume=""
        )
