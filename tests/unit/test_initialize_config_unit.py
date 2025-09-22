"""Unit tests for configuration and initialization module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import FrozenInstanceError
from libs.InitializeConfig import (
    ConfigurationManager, TestEnvironmentConfig, ModuleConfigLoader,
    InitializeConfig
)
from libs.exceptions import ConfigurationException


class TestConfigurationManagerUnit:
    """Unit tests for ConfigurationManager class."""
    
    def test_load_config_success(self):
        """Test successful configuration loading."""
        with patch('libs.InitializeConfig.ModuleConfigLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader_class.return_value = mock_loader
            
            mock_config = TestEnvironmentConfig(
                uuid="test-uuid",
                billing_group_id="bg-123",
                project_id=["proj-1"],
                campaign_id=["camp-1"]
            )
            mock_loader.load.return_value = mock_config
            
            manager = ConfigurationManager(member="kr", month="2024-01")
            config = manager.load_config("alpha", "kr")
            
            assert config.uuid == "test-uuid"
            assert config.billing_group_id == "bg-123"
            mock_loader.load.assert_called_once_with("alpha", "kr")
    
    @patch('libs.InitializeConfig.importlib.import_module')
    def test_load_config_module_not_found(self, mock_import):
        """Test configuration loading when module not found."""
        mock_import.side_effect = ImportError("Module not found")
        
        loader = ModuleConfigLoader()
        
        with pytest.raises(ConfigurationException) as exc_info:
            loader.load("invalid", "kr")
        
        assert "Configuration module not found" in str(exc_info.value)
    
    @patch('libs.InitializeConfig.importlib.import_module')
    def test_load_config_missing_test_config(self, mock_import):
        """Test configuration loading when test_config is missing."""
        mock_module = Mock()
        # Module exists but no test_config or config attribute
        mock_import.return_value = mock_module
        
        loader = ModuleConfigLoader()
        
        with pytest.raises(ConfigurationException) as exc_info:
            loader.load("alpha", "kr")
        
        assert "Invalid configuration type" in str(exc_info.value)
    
    @patch('libs.InitializeConfig.importlib.import_module')
    def test_load_config_dict_format(self, mock_import):
        """Test loading configuration from dictionary format."""
        mock_module = Mock()
        mock_module.test_config = {
            "uuid": "dict-uuid",
            "billing_group_id": "dict-bg-123",
            "project_id": ["proj-1"],
            "appkey": ["app-1"],
            "campaign_id": ["camp-1"]
        }
        mock_import.return_value = mock_module
        
        loader = ModuleConfigLoader()
        config = loader.load("alpha", "kr")
        
        assert config.uuid == "dict-uuid"
        assert config.billing_group_id == "dict-bg-123"
        assert config.project_id == ["proj-1"]
    
    @patch('libs.InitializeConfig.importlib.import_module')
    def test_load_config_legacy_format(self, mock_import):
        """Test loading configuration from legacy config attribute."""
        mock_module = Mock()
        # Using legacy 'config' name instead of 'test_config'
        mock_module.config = {
            "uuid": "legacy-uuid",
            "billing_group_id": "legacy-bg",
            "project_id": ["proj-legacy"]
        }
        mock_import.return_value = mock_module
        
        loader = ModuleConfigLoader()
        config = loader.load("alpha", "kr")
        
        assert config.uuid == "legacy-uuid"
        assert config.billing_group_id == "legacy-bg"
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        config = TestEnvironmentConfig(
            uuid="test-uuid",
            billing_group_id="bg-123"
        )
        
        manager = ConfigurationManager(member="kr", month="2024-01")
        # Should not raise exception
        manager.validate_config(config)
    
    def test_validate_config_empty_uuid(self):
        """Test configuration validation with empty UUID."""
        with pytest.raises(ConfigurationException) as exc_info:
            TestEnvironmentConfig(
                uuid="",  # Empty UUID
                billing_group_id="bg-123"
            )
        
        assert "UUID cannot be empty" in str(exc_info.value)
    
    def test_validate_config_empty_billing_group_id(self):
        """Test configuration validation with empty billing group ID."""
        with pytest.raises(ConfigurationException) as exc_info:
            TestEnvironmentConfig(
                uuid="test-uuid",
                billing_group_id=""  # Empty billing group ID
            )
        
        assert "Billing group ID cannot be empty" in str(exc_info.value)


class TestTestEnvironmentConfig:
    """Unit tests for TestEnvironmentConfig dataclass."""
    
    def test_dataclass_creation_with_defaults(self):
        """Test creating config with default values."""
        config = TestEnvironmentConfig(
            uuid="test-uuid",
            billing_group_id="bg-123"
        )
        
        assert config.uuid == "test-uuid"
        assert config.billing_group_id == "bg-123"
        assert config.project_id == []
        assert config.appkey == []
        assert config.campaign_id == []
        assert config.give_campaign_id == []
        assert config.paid_campaign_id == []
    
    def test_dataclass_creation_with_all_fields(self):
        """Test creating config with all fields."""
        config = TestEnvironmentConfig(
            uuid="test-uuid",
            billing_group_id="bg-123",
            project_id=["proj-1", "proj-2"],
            appkey=["app-1", "app-2"],
            campaign_id=["camp-1"],
            give_campaign_id=["give-1"],
            paid_campaign_id=["paid-1"]
        )
        
        assert len(config.project_id) == 2
        assert len(config.appkey) == 2
        assert config.campaign_id == ["camp-1"]
        assert config.give_campaign_id == ["give-1"]
        assert config.paid_campaign_id == ["paid-1"]
    
    def test_dataclass_immutability(self):
        """Test that config is immutable (frozen)."""
        config = TestEnvironmentConfig(
            uuid="test-uuid",
            billing_group_id="bg-123"
        )
        
        with pytest.raises(FrozenInstanceError):
            config.uuid = "new-uuid"
    
    def test_to_dict_method(self):
        """Test converting config to dictionary."""
        config = TestEnvironmentConfig(
            uuid="test-uuid",
            billing_group_id="bg-123",
            project_id=["proj-1"],
            campaign_id=["camp-1"]
        )
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["uuid"] == "test-uuid"
        assert config_dict["billing_group_id"] == "bg-123"
        assert config_dict["project_id"] == ["proj-1"]
        assert config_dict["campaign_id"] == ["camp-1"]


class TestInitializeConfigLegacy:
    """Unit tests for legacy InitializeConfig class."""
    
    @patch('libs.InitializeConfig.ConfigurationManager')
    @patch('libs.InitializeConfig.DefaultManagerFactory')
    def test_init_legacy(self, mock_factory_class, mock_config_manager_class):
        """Test legacy initialization."""
        # Setup mocks
        mock_config_manager = Mock()
        mock_config_manager_class.return_value = mock_config_manager
        
        mock_config = TestEnvironmentConfig(
            uuid="test-uuid",
            billing_group_id="bg-123",
            project_id=["proj-1"],
            appkey=["app-1"],
            campaign_id=["camp-1"]
        )
        mock_config_manager.load_config.return_value = mock_config
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_services = {
            "payment_manager": Mock(),
            "credit_manager": Mock(),
            "contract_manager": Mock()
        }
        mock_factory.create_services.return_value = mock_services
        
        # Create legacy instance
        init_config = InitializeConfig(env="alpha", member="kr", month="2024-01")
        
        # Check attributes
        assert init_config.uuid == "test-uuid"
        assert init_config.billing_group_id == "bg-123"
        assert init_config.project_id == ["proj-1"]
        assert init_config.appkey == ["app-1"]
        assert init_config.campaign_id == ["camp-1"]
    
    def test_property_access(self):
        """Test property access patterns."""
        with patch('libs.InitializeConfig.ConfigurationManager') as mock_cm, \
             patch('libs.InitializeConfig.DefaultManagerFactory'):
            
            mock_config = TestEnvironmentConfig(
                uuid="test-uuid",
                billing_group_id="bg-123",
                project_id=["proj-1"],
                appkey=["app-1"],
                campaign_id=["camp-1"]
            )
            mock_cm.return_value.load_config.return_value = mock_config
            
            init_config = InitializeConfig(env="alpha", member="kr", month="2024-01")
            
            # Test properties
            assert hasattr(init_config, "uuid")
            assert hasattr(init_config, "billing_group_id")
            assert hasattr(init_config, "project_id")
            assert init_config.uuid == "test-uuid"
            assert init_config.billing_group_id == "bg-123"
    
    @patch('libs.InitializeConfig.ConfigurationManager')
    @patch('libs.InitializeConfig.DefaultManagerFactory')
    def test_legacy_service_access(self, mock_factory_class, mock_config_manager_class):
        """Test accessing services through legacy interface."""
        mock_payment_manager = Mock()
        mock_credit_manager = Mock()
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_factory.create_services.return_value = {
            "payment_manager": mock_payment_manager,
            "credit_manager": mock_credit_manager
        }
        
        mock_config_manager = Mock()
        mock_config_manager_class.return_value = mock_config_manager
        mock_config_manager.load_config.return_value = TestEnvironmentConfig(
            uuid="test-uuid",
            billing_group_id="bg-123"
        )
        
        init_config = InitializeConfig(env="alpha", member="kr", month="2024-01")
        
        # Access services
        assert init_config.payment_manager is mock_payment_manager
        assert init_config.credit_manager is mock_credit_manager
    
    @patch('libs.InitializeConfig.ConfigurationManager')
    @patch('libs.InitializeConfig.DefaultManagerFactory')
    @patch('libs.InitializeConfig.logger')
    def test_logging_on_init(self, mock_logger, mock_factory_class, mock_config_manager_class):
        """Test that initialization is logged."""
        mock_config_manager = Mock()
        mock_config_manager_class.return_value = mock_config_manager
        mock_config_manager.load_config.return_value = TestEnvironmentConfig(
            uuid="test-uuid",
            billing_group_id="bg-123"
        )
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_factory.create_services.return_value = {}
        
        InitializeConfig(env="alpha", member="kr", month="2024-01")
        
        # Verify logging occurred
        assert mock_logger.info.called


# Additional edge case tests
class TestConfigurationEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_list_fields(self):
        """Test configuration with empty list fields."""
        config = TestEnvironmentConfig(
            uuid="test-uuid",
            billing_group_id="bg-123",
            project_id=[],
            appkey=[],
            campaign_id=[]
        )
        
        # Empty lists should be allowed
        assert config.project_id == []
        assert config.appkey == []
        assert config.campaign_id == []
    
    def test_special_characters_in_ids(self):
        """Test configuration with special characters."""
        config = TestEnvironmentConfig(
            uuid="test-uuid-123!@#",
            billing_group_id="bg-123/456#test",
            project_id=["proj@123", "proj#456"]
        )
        
        # Special characters should be preserved
        assert config.uuid == "test-uuid-123!@#"
        assert config.billing_group_id == "bg-123/456#test"
        assert "proj@123" in config.project_id
    
    @patch('libs.InitializeConfig.importlib.import_module')
    def test_config_with_extra_fields(self, mock_import):
        """Test loading config with extra fields (should be ignored)."""
        mock_module = Mock()
        mock_module.test_config = {
            "uuid": "test-uuid",
            "billing_group_id": "bg-123",
            "extra_field": "should_be_ignored",
            "another_extra": 12345
        }
        mock_import.return_value = mock_module
        
        loader = ModuleConfigLoader()
        config = loader.load("alpha", "kr")
        
        # Extra fields should be ignored, not cause errors
        assert config.uuid == "test-uuid"
        assert config.billing_group_id == "bg-123"
        assert not hasattr(config, "extra_field")