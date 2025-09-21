"""Configuration and initialization management for billing tests."""

import contextlib
import importlib
import logging
from dataclasses import dataclass, field
from typing import Any

from .adjustment import AdjustmentManager
from .calculation import CalculationManager
from .constants import PaymentStatus
from .Contract import ContractManager
from .Credit import CreditManager
from .exceptions import ConfigurationException
from .Metering import MeteringManager
from .Payments import PaymentManager

logger = logging.getLogger(__name__)


@dataclass
class TestEnvironmentConfig:
    """Configuration for test environment."""

    uuid: str
    billing_group_id: str
    project_id: list[str] = field(default_factory=list)
    appkey: list[str] = field(default_factory=list)
    campaign_id: list[str] = field(default_factory=list)
    give_campaign_id: list[str] = field(default_factory=list)
    paid_campaign_id: list[str] = field(default_factory=list)


class ConfigurationManager:
    """Manages test configuration and environment setup."""

    def __init__(self, environment: str, member: str, month: str) -> None:
        """Initialize configuration manager.

        Args:
            environment: Environment name (e.g., 'alpha')
            member: Member country code (e.g., 'kr', 'jp', 'etc')
            month: Target month in YYYY-MM format

        Raises:
            ConfigurationException: If configuration cannot be loaded
        """
        self.environment = environment
        self.member = member
        self.month = month

        # Load configuration
        self.config = self._load_configuration(environment, member)

        # Initialize managers
        self._init_managers()

    def _load_configuration(
        self, environment: str, member: str
    ) -> TestEnvironmentConfig:
        """Load configuration from config module.

        Args:
            environment: Environment name
            member: Member country code

        Returns:
            Test environment configuration

        Raises:
            ConfigurationException: If configuration cannot be loaded
        """
        try:
            # Dynamically import configuration module
            module_name = f"config.{environment}_{member}"
            config_module = importlib.import_module(module_name)

            if not hasattr(config_module, "config"):
                msg = f"Configuration module {module_name} does not have 'config' attribute"
                raise ConfigurationException(
                    msg
                )

            config_data = config_module.config

            # Validate required fields
            required_fields = ["uuid", "billing_group_id"]
            for field in required_fields:
                if field not in config_data:
                    msg = f"Required field '{field}' missing in configuration"
                    raise ConfigurationException(
                        msg
                    )

            # Create configuration object
            return TestEnvironmentConfig(
                uuid=config_data["uuid"],
                billing_group_id=config_data["billing_group_id"],
                project_id=config_data.get("project_id", []),
                appkey=config_data.get("appkey", []),
                campaign_id=config_data.get("campaign_id", []),
                give_campaign_id=config_data.get("give_campaign_id", []),
                paid_campaign_id=config_data.get("paid_campaign_id", []),
            )

        except ImportError as e:
            msg = f"Failed to import configuration module for {environment}_{member}: {e}"
            raise ConfigurationException(
                msg
            )
        except Exception as e:
            msg = f"Failed to load configuration: {e}"
            raise ConfigurationException(msg)

    def _init_managers(self) -> None:
        """Initialize billing managers."""
        self.payment_manager = PaymentManager(self.month, self.config.uuid)
        self.credit_manager = CreditManager(self.config.uuid)
        self.metering_manager = MeteringManager(self.month)
        self.calculation_manager = CalculationManager(self.month, self.config.uuid)
        self.adjustment_manager = AdjustmentManager(self.month)

        if self.config.billing_group_id:
            self.contract_manager = ContractManager(
                self.month, self.config.billing_group_id
            )

    def prepare_test_environment(self) -> None:
        """Prepare test environment by setting payment status to REGISTERED."""
        logger.info("Preparing test environment")

        try:
            # Get current payment status
            payment_group_id, payment_status = self.payment_manager.get_payment_status()

            if not payment_group_id:
                logger.warning("No payment found for the specified month")
                return

            # Handle different payment statuses using match-case
            match payment_status:
                case PaymentStatus.PAID.value:
                    logger.info("Payment is PAID, cancelling and changing to REGISTERED")
                    self.payment_manager.cancel_payment(payment_group_id)
                    self.payment_manager.change_payment_status(payment_group_id)
                case PaymentStatus.READY.value:
                    logger.info("Payment is READY, changing to REGISTERED")
                    self.payment_manager.change_payment_status(payment_group_id)
                case PaymentStatus.REGISTERED.value:
                    logger.info("Payment is already REGISTERED")
                case _:
                    logger.warning("Unknown payment status: %s", payment_status)

        except Exception as e:
            logger.exception("Failed to prepare test environment: %s", e)
            raise

    def clean_test_data(self) -> dict[str, Any]:
        """Clean all test data for fresh start.

        Returns:
            Summary of cleaning operations
        """
        logger.info("Cleaning test data")

        results = {
            "metering": False,
            "contracts": False,
            "adjustments": False,
            "calculations": False,
        }

        # Clean metering data
        try:
            if self.config.appkey:
                self.metering_manager.delete_metering(self.config.appkey)
                results["metering"] = True
                logger.info("Cleaned metering data")
        except Exception as e:
            logger.exception("Failed to clean metering data: %s", e)

        # Clean contracts
        try:
            if hasattr(self, "contract_manager"):
                self.contract_manager.delete_contract()
                results["contracts"] = True
                logger.info("Cleaned contracts")
        except Exception as e:
            logger.exception("Failed to clean contracts: %s", e)

        # Clean adjustments
        try:
            results["adjustments"] = self._clean_adjustments()
            logger.info("Cleaned adjustments")
        except Exception as e:
            logger.exception("Failed to clean adjustments: %s", e)

        # Clean calculations
        try:
            self.calculation_manager.delete_resources()
            results["calculations"] = True
            logger.info("Cleaned calculation resources")
        except Exception as e:
            logger.exception("Failed to clean calculations: %s", e)

        return results

    def _clean_adjustments(self) -> bool:
        """Clean all adjustments for projects and billing groups."""
        cleaned = False

        # Clean project adjustments
        for project_id in self.config.project_id:
            try:
                count = self.adjustment_manager.delete_all_adjustments(
                    adjustment_target="Project", target_id=project_id
                )
                if count > 0:
                    cleaned = True
                    logger.info("Deleted {count} adjustments for project %s", project_id)
            except Exception as e:
                logger.exception("Failed to clean adjustments for project {project_id}: %s", e
                )

        # Clean billing group adjustments
        if self.config.billing_group_id:
            try:
                count = self.adjustment_manager.delete_all_adjustments(
                    adjustment_target="BillingGroup",
                    target_id=self.config.billing_group_id,
                )
                if count > 0:
                    cleaned = True
                    logger.info("Deleted %s adjustments for billing group", count)
            except Exception as e:
                logger.exception("Failed to clean billing group adjustments: %s", e)

        return cleaned

    def verify_assertion(
        self,
        statements: float,
        payments: float,
        expected_result: float,
        tolerance: float = 0.01,
    ) -> bool:
        """Verify billing assertion with tolerance.

        Args:
            statements: Statement amount
            payments: Payment amount
            expected_result: Expected result
            tolerance: Acceptable difference tolerance

        Returns:
            True if assertion passes, False otherwise
        """
        diff = abs(statements - payments)
        expected_diff = abs(expected_result - payments)

        passed = diff <= tolerance and expected_diff <= tolerance

        if passed:
            logger.info(
                "Assertion PASSED - Statements: %s, Payments: %s, Expected: %s",
                statements,
                payments,
                expected_result,
            )
        else:
            logger.error(
                "Assertion FAILED - Statements: %s, Payments: %s, Expected: %s, Diff: %s, Expected diff: %s",
                statements,
                payments,
                expected_result,
                diff,
                expected_diff,
            )

        return passed


# Backward compatibility wrapper
class InitializeConfig:
    """Legacy wrapper for backward compatibility."""

    def __init__(self, env: str, member: str, month: str) -> None:
        self.month = month
        self.member = member

        try:
            self._manager = ConfigurationManager(env, member, month)

            # Copy configuration attributes
            config = self._manager.config
            self.uuid = config.uuid
            self.billing_group_id = config.billing_group_id
            self.project_id = config.project_id
            self.appkey = config.appkey
            self.campaign_id = config.campaign_id
            self.give_campaign_id = config.give_campaign_id
            self.paid_campaign_id = config.paid_campaign_id

        except Exception:
            # Fall back to legacy configuration loading
            config_module = importlib.import_module(f"config.{env}_{member}")
            config_data = config_module.config

            self.uuid = config_data["uuid"]
            self.billing_group_id = config_data["billing_group_id"]
            self.project_id = config_data["project_id"]
            self.appkey = config_data["appkey"]
            self.campaign_id = config_data["campaign_id"]
            self.give_campaign_id = config_data["give_campaign_id"]
            self.paid_campaign_id = config_data["paid_campaign_id"]
            self._manager = None

    def before_test(self) -> None:
        """Legacy method for test preparation."""
        if self._manager:
            with contextlib.suppress(Exception):
                self._manager.prepare_test_environment()
        else:
            # Legacy implementation
            from . import Payments

            paymentsObj = Payments(self.month)
            paymentsObj.uuid = self.uuid
            pgId, pgStatusCode = paymentsObj.inquiry_payment()

            match pgStatusCode:
                case "PAID":
                    paymentsObj.cancel_payment(pgId)
                    paymentsObj.change_payment(pgId)
                case "READY":
                    paymentsObj.change_payment(pgId)
                case "REGISTERED":
                    pass
                case _:
                    pass

    def clean_data(self) -> None:
        """Legacy method for cleaning test data."""
        if self._manager:
            with contextlib.suppress(Exception):
                self._manager.clean_test_data()
        else:
            # Legacy implementation
            self.clean_metering()
            self.clean_contract()
            self.clean_adjustment()
            self.clean_calculation()

    def clean_metering(self) -> None:
        """Legacy method for cleaning metering."""
        from . import Metering

        meteringObj = Metering(self.month)
        meteringObj.appkey = self.appkey
        meteringObj.delete_metering()

    def clean_contract(self) -> None:
        """Legacy method for cleaning contracts."""
        from . import Contract

        contractObj = Contract(self.month, self.billing_group_id)
        contractObj.delete_contract()

    def clean_adjustment(self) -> None:
        """Legacy method for cleaning adjustments."""
        from . import Adjustments

        adjObj = Adjustments(self.month)

        # Clean project adjustments
        for pid in self.project_id:
            adjlist = adjObj.inquiry_adjustment(
                adjustmentTarget="Project", projectId=pid
            )
        if adjlist:
            adjObj.delete_adjustment(adjlist)

        # Clean billing group adjustments
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="BillingGroup", billingGroupid=self.billing_group_id
        )
        if adjlist:
            adjObj.delete_adjustment(adjlist)

    def clean_calculation(self) -> None:
        """Legacy method for cleaning calculations."""
        from . import Calculation

        calcObj = Calculation(self.month, self.uuid)
        calcObj.delete_resources()

    def common_test(self):
        """Legacy method for common test execution flow."""
        from . import Calculation, Payments

        # Perform calculation
        calcObj = Calculation(self.month, self.uuid)
        calcObj.check_stable()

        # Get payment info
        paymentsObj = Payments(self.month)
        paymentsObj.uuid = self.uuid
        pgId, _pgStatusCode = paymentsObj.inquiry_payment()

        # Make payment
        if pgId:
            paymentsObj.payment(pgId)

        # Get billing details from API
        from . import http_client
        from config.url import BASE_BILLING_URL
        
        client = http_client.BillingAPIClient(BASE_BILLING_URL)
        billing_detail = client.get(
            f"billing/v5.0/bills/detail",
            params={"uuid": self.uuid, "month": self.month}
        )
        
        # Extract statement details from billing response
        statements = {
            "charge": billing_detail.get("charge", 0),
            "totalAmount": billing_detail.get("totalAmount", 0),
            "discountAmount": billing_detail.get("discountAmount", 0),
            "vat": billing_detail.get("vat", 0),
            "totalCredit": billing_detail.get("totalCredit", 0)
        }

        # Calculate actual payment amount after credits
        credit_amount = billing_detail.get("totalCredit", 0)
        charge = billing_detail.get("charge", 0)
        total_amount = billing_detail.get("totalAmount", 0)
        
        # The totalAmount from API already has credits applied in mock server
        # So we just use it directly as the payment amount
        total_payments = total_amount

        return statements, total_payments

    def verify_assert(self, **kwargs):
        """Legacy method for assertion verification."""
        statements = kwargs.get("statements", 0)
        payments = kwargs.get("payments", 0)
        expected_result = kwargs.get("expected_result", 0)

        if self._manager:
            return self._manager.verify_assertion(statements, payments, expected_result)
        # Legacy simple check
        passed = (statements == payments) and (payments == expected_result)
        if passed:
            pass
        else:
            pass
        return passed
