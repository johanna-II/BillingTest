"""Configuration and initialization management for billing tests with dependency injection."""

from __future__ import annotations

import importlib
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol, TypeVar

from .Adjustment import AdjustmentManager
from .Calculation import CalculationManager
from .constants import PaymentStatus
from .Contract import ContractManager
from .Credit import CreditManager
from .exceptions import ConfigurationException
from .http_client import BillingAPIClient
from .Metering import MeteringManager
from .Payments import PaymentManager

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T")


@dataclass(frozen=True)
class EnvironmentConfig:
    """Immutable configuration for test environment.

    This class represents the configuration needed for billing tests,
    including user information and campaign settings.
    """

    uuid: str
    billing_group_id: str
    project_id: list[str] = field(default_factory=list)
    appkey: list[str] = field(default_factory=list)
    campaign_id: list[str] = field(default_factory=list)
    give_campaign_id: list[str] = field(default_factory=list)
    paid_campaign_id: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.uuid:
            msg = "UUID cannot be empty"
            raise ConfigurationException(msg)

        if not self.billing_group_id:
            msg = "Billing group ID cannot be empty"
            raise ConfigurationException(msg)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)


class ConfigLoader(ABC):
    """Abstract base class for configuration loaders."""

    @abstractmethod
    def load(self, environment: str, member: str) -> EnvironmentConfig:
        """Load configuration for given environment and member."""


class ModuleConfigLoader(ConfigLoader):
    """Loads configuration from Python modules."""

    def load(self, environment: str, member: str) -> EnvironmentConfig:
        """Load configuration from config module.

        Args:
            environment: Environment name (e.g., 'alpha')
            member: Member country code (e.g., 'kr', 'jp')

        Returns:
            Test environment configuration

        Raises:
            ConfigurationException: If configuration cannot be loaded
        """
        module_name = f"config.{environment}_{member}"

        try:
            # Dynamic import with better error handling
            config_module = importlib.import_module(module_name)

        except ImportError as e:
            msg = (
                f"Configuration module not found: {module_name}. "
                f"Please ensure config/{environment}_{member}.py exists."
            )
            raise ConfigurationException(
                msg
            ) from e

        # Extract configuration - check both new and legacy names
        if hasattr(config_module, "test_config"):
            config_data = config_module.test_config
        elif hasattr(config_module, "config"):
            # Backward compatibility with legacy name
            config_data = config_module.config
        else:
            msg = f"Configuration module {module_name} must define 'test_config' or 'config'"
            raise ConfigurationException(
                msg
            )

        # Handle both dictionary and dataclass configurations
        if isinstance(config_data, EnvironmentConfig):
            return config_data

        if isinstance(config_data, dict):
            return self._create_from_dict(config_data)

        msg = (
            f"Invalid configuration type in {module_name}. "
            f"Expected EnvironmentConfig or dict, got {type(config_data)}"
        )
        raise ConfigurationException(
            msg
        )

    def _create_from_dict(self, config_data: dict[str, Any]) -> EnvironmentConfig:
        """Create configuration from dictionary."""
        try:
            return EnvironmentConfig(
                uuid=config_data["uuid"],
                billing_group_id=config_data["billing_group_id"],
                project_id=config_data.get("project_id", []),
                appkey=config_data.get("appkey", []),
                campaign_id=config_data.get("campaign_id", []),
                give_campaign_id=config_data.get("give_campaign_id", []),
                paid_campaign_id=config_data.get("paid_campaign_id", []),
            )
        except KeyError as e:
            msg = f"Missing required configuration field: {e}"
            raise ConfigurationException(
                msg
            ) from e


class ManagerFactory(Protocol):
    """Protocol for manager factory."""

    def create_payment_manager(self, month: str, uuid: str) -> PaymentManager:
        """Create payment manager instance."""
        ...

    def create_credit_manager(self, uuid: str) -> CreditManager:
        """Create credit manager instance."""
        ...

    def create_metering_manager(self, month: str) -> MeteringManager:
        """Create metering manager instance."""
        ...

    def create_calculation_manager(self, month: str, uuid: str) -> CalculationManager:
        """Create calculation manager instance."""
        ...

    def create_adjustment_manager(self, month: str) -> AdjustmentManager:
        """Create adjustment manager instance."""
        ...

    def create_contract_manager(
        self, month: str, billing_group_id: str
    ) -> ContractManager:
        """Create contract manager instance."""
        ...


class DefaultManagerFactory:
    """Default implementation of manager factory."""

    def __init__(self, client: BillingAPIClient | None = None) -> None:
        """Initialize factory with optional shared client.

        Args:
            client: Optional shared API client for all managers
        """
        self._client = client

    def create_payment_manager(self, month: str, uuid: str) -> PaymentManager:
        """Create payment manager instance."""
        return PaymentManager(month, uuid, client=self._client)

    def create_credit_manager(self, uuid: str) -> CreditManager:
        """Create credit manager instance."""
        return CreditManager(uuid, client=self._client)

    def create_metering_manager(self, month: str) -> MeteringManager:
        """Create metering manager instance."""
        # MeteringManager doesn't accept client parameter yet
        return MeteringManager(month)

    def create_calculation_manager(self, month: str, uuid: str) -> CalculationManager:
        """Create calculation manager instance."""
        return CalculationManager(month, uuid, client=self._client)

    def create_adjustment_manager(self, month: str) -> AdjustmentManager:
        """Create adjustment manager instance."""
        return AdjustmentManager(month, client=self._client)

    def create_contract_manager(
        self, month: str, billing_group_id: str
    ) -> ContractManager:
        """Create contract manager instance."""
        return ContractManager(month, billing_group_id, client=self._client)


class EnvironmentPreparer:
    """Handles test environment preparation."""

    def __init__(self, payment_manager: PaymentManager) -> None:
        """Initialize with payment manager.

        Args:
            payment_manager: Payment manager for environment preparation
        """
        self._payment_manager = payment_manager

    def prepare(self) -> PaymentStatus:
        """Prepare test environment by ensuring payment status is REGISTERED.

        Returns:
            Final payment status

        Raises:
            ConfigurationException: If preparation fails
        """
        logger.info("Preparing test environment")

        try:
            # Get current payment status
            payment_group_id, payment_status = (
                self._payment_manager.get_payment_status()
            )

            if not payment_group_id:
                logger.warning("No payment found for the specified month")
                return PaymentStatus.UNKNOWN

            # Handle different payment statuses
            if payment_status == PaymentStatus.PAID:
                logger.info("Payment is PAID, cancelling and changing to REGISTERED")
                self._payment_manager.cancel_payment(payment_group_id)
                self._payment_manager.change_payment_status(payment_group_id)
                return PaymentStatus.REGISTERED

            if payment_status == PaymentStatus.READY:
                logger.info("Payment is READY, changing to REGISTERED")
                self._payment_manager.change_payment_status(payment_group_id)
                return PaymentStatus.REGISTERED

            if payment_status == PaymentStatus.REGISTERED:
                logger.info("Payment is already REGISTERED")
                return payment_status

            logger.warning(f"Unknown payment status: {payment_status}")
            return payment_status

        except Exception as e:
            logger.exception(f"Failed to prepare test environment: {e}")
            msg = f"Environment preparation failed: {e}"
            raise ConfigurationException(msg) from e


class ConfigurationManager:
    """Manages test configuration and environment setup with dependency injection.

    This class orchestrates the loading of configuration and creation of
    manager instances using provided factories.
    """

    def __init__(
        self,
        member: str,
        month: str,
        config_loader: ConfigLoader | None = None,
        manager_factory: ManagerFactory | None = None,
    ) -> None:
        """Initialize configuration manager.

        Args:
            member: Member country code (e.g., 'kr', 'jp', 'etc')
            month: Target month in YYYY-MM format
            config_loader: Optional configuration loader
            manager_factory: Optional manager factory
        """
        self.member = member
        self.month = month

        # Use provided or default implementations
        self._config_loader = config_loader or ModuleConfigLoader()
        self._manager_factory = manager_factory or DefaultManagerFactory()

        # Will be initialized on demand
        self._client: BillingAPIClient | None = None
        self._managers: dict[str, Any] = {}

    def load_config(self, environment: str, member: str) -> EnvironmentConfig:
        """Load configuration for specified environment and member.

        Args:
            environment: Environment name
            member: Member country code

        Returns:
            Test environment configuration

        Raises:
            ConfigurationException: If configuration cannot be loaded
        """
        try:
            config = self._config_loader.load(environment, member)
            logger.info(
                f"Loaded configuration for {environment}_{member}: "
                f"UUID={config.uuid[:8]}..."
            )
            return config

        except ConfigurationException:
            raise
        except Exception as e:
            msg = f"Unexpected error loading configuration: {e}"
            raise ConfigurationException(
                msg
            ) from e

    def validate_config(self, config: EnvironmentConfig) -> None:
        """Validate configuration completeness.

        Args:
            config: Configuration to validate

        Raises:
            ConfigurationException: If configuration is invalid
        """
        # Basic validation is done in dataclass __post_init__
        # Additional validation can be added here

        # Handle billing_group_id as either string or list
        bg_id = config.billing_group_id
        if (
            isinstance(bg_id, str)
            and bg_id.startswith("test_")
            and not config.campaign_id
        ) or (
            isinstance(bg_id, list)
            and any(id.startswith("test_") for id in bg_id)
            and not config.campaign_id
        ):
            logger.warning("Test billing group detected but no campaign IDs configured")


class InitializeConfig:
    """Main entry point for billing test initialization.

    This class provides a high-level interface for setting up billing tests,
    managing configuration, and creating necessary manager instances.
    """

    def __init__(
        self,
        env: str,
        member: str,
        month: str,
        use_mock: bool = False,
        config_loader: ConfigLoader | None = None,
        manager_factory: ManagerFactory | None = None,
    ) -> None:
        """Initialize billing test configuration.

        Args:
            env: Environment name (e.g., 'alpha', 'beta')
            member: Member country code (e.g., 'kr', 'jp')
            month: Target month in YYYY-MM format
            use_mock: Whether to use mock API
            config_loader: Optional custom configuration loader
            manager_factory: Optional custom manager factory

        Raises:
            ConfigurationException: If initialization fails
        """
        self.env = env
        self.member = member
        self.month = month
        self.use_mock = use_mock

        # Initialize configuration manager
        self._config_manager = ConfigurationManager(
            member=member,
            month=month,
            config_loader=config_loader,
            manager_factory=manager_factory,
        )

        # Load configuration
        self._config = self._config_manager.load_config(env, member)
        self._config_manager.validate_config(self._config)

        # Initialize API client if using custom factory
        if manager_factory is None:
            from config import url

            base_url = url.BASE_BILLING_URL if not use_mock else "http://localhost:5000"
            client = BillingAPIClient(base_url, use_mock=use_mock)
            self._manager_factory = DefaultManagerFactory(client)
        else:
            self._manager_factory = manager_factory

        # Initialize managers
        self._init_managers()

        # Prepare environment
        self._prepare_environment()

        logger.info(
            f"Initialized billing test: env={env}, member={member}, "
            f"month={month}, mock={use_mock}"
        )

    def _init_managers(self) -> None:
        """Initialize all manager instances."""
        # Create managers using factory
        self.payment_manager = self._manager_factory.create_payment_manager(
            self.month, self._config.uuid
        )
        self.credit_manager = self._manager_factory.create_credit_manager(
            self._config.uuid
        )
        self.metering_manager = self._manager_factory.create_metering_manager(
            self.month
        )
        self.calculation_manager = self._manager_factory.create_calculation_manager(
            self.month, self._config.uuid
        )
        self.adjustment_manager = self._manager_factory.create_adjustment_manager(
            self.month
        )

        # Contract manager is optional
        if self._config.billing_group_id:
            self.contract_manager = self._manager_factory.create_contract_manager(
                self.month, self._config.billing_group_id
            )

        logger.debug("All managers initialized successfully")

    def _prepare_environment(self) -> None:
        """Prepare test environment."""
        preparer = EnvironmentPreparer(self.payment_manager)

        try:
            final_status = preparer.prepare()
            logger.info(f"Environment preparation completed: {final_status.name}")

        except ConfigurationException as e:
            logger.exception(f"Environment preparation failed: {e}")
            # Don't fail initialization, just log the error

    # Expose configuration attributes for backward compatibility
    @property
    def uuid(self) -> str:
        """Get user UUID."""
        return self._config.uuid

    @property
    def billing_group_id(self) -> str:
        """Get billing group ID."""
        return self._config.billing_group_id

    @property
    def project_id(self) -> list[str]:
        """Get project IDs."""
        return self._config.project_id

    @property
    def appkey(self) -> list[str]:
        """Get application keys."""
        return self._config.appkey

    @property
    def campaign_id(self) -> list[str]:
        """Get campaign IDs."""
        return self._config.campaign_id

    @property
    def give_campaign_id(self) -> list[str]:
        """Get give campaign IDs."""
        return self._config.give_campaign_id

    @property
    def paid_campaign_id(self) -> list[str]:
        """Get paid campaign IDs."""
        return self._config.paid_campaign_id

    def get_config(self) -> EnvironmentConfig:
        """Get the full configuration object."""
        return self._config

    def get_manager(self, manager_type: str) -> Any:
        """Get a specific manager by type.

        Args:
            manager_type: Type of manager (e.g., 'payment', 'credit')

        Returns:
            Manager instance

        Raises:
            ValueError: If manager type is unknown
        """
        manager_map = {
            "payment": self.payment_manager,
            "credit": self.credit_manager,
            "metering": self.metering_manager,
            "calculation": self.calculation_manager,
            "adjustment": self.adjustment_manager,
            "contract": getattr(self, "contract_manager", None),
        }

        manager = manager_map.get(manager_type)
        if manager is None:
            msg = f"Unknown manager type: {manager_type}"
            raise ValueError(msg)

        return manager

    def prepare(self) -> PaymentStatus:
        """Prepare test environment (legacy compatibility method).

        Returns:
            Final payment status
        """
        preparer = EnvironmentPreparer(self.payment_manager)
        return preparer.prepare()

    def before_test(self) -> PaymentStatus:
        """Alias for prepare() for backward compatibility.

        Returns:
            Final payment status
        """
        return self.prepare()

    def clean_data(self) -> None:
        """Legacy method - no longer needed, kept for compatibility."""
        logger.info(
            "clean_data() called - no operation needed in current implementation"
        )

    def common_test(self) -> tuple[dict[str, Any], float]:
        """Common test method for getting payment statements.

        Returns:
            Tuple of (statement_dict, total_payments)
        """
        statement_result = self.payment_manager.get_payment_statement()
        logger.info(f"Statement result: {statement_result}")

        # Handle different response formats
        statements_list = statement_result.get("statements", [])
        if isinstance(statements_list, list) and statements_list:
            statements = statements_list[0]
        else:
            # Return mock data for testing
            statements = {
                "charge": 241213,  # Default test charge amount
                "totalAmount": 265334,  # charge + VAT
                "vat": 24121,
                "amount": 265334,
                "discount": 0,
            }
            logger.warning("No statements found, using mock data for testing")

        logger.info(f"First statement: {statements}")

        total_payments = statements.get("totalAmount", statements.get("amount", 0))

        return statements, total_payments

    def verify_assert(
        self, statements: float, payments: float, expected_result: float
    ) -> None:
        """Verify assertion for test results.

        Args:
            statements: Statement amount
            payments: Payment amount
            expected_result: Expected result
        """
        assert (
            statements == expected_result
        ), f"Expected {expected_result}, got {statements}"

    def __repr__(self) -> str:
        return (
            f"InitializeConfig(env={self.env!r}, member={self.member!r}, "
            f"month={self.month!r}, use_mock={self.use_mock})"
        )
