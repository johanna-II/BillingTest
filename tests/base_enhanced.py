"""Enhanced base test classes to reduce duplication."""

from __future__ import annotations

import pytest
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from libs import InitializeConfig
from libs.dependency_injection import configure_dependencies, get_container
from libs.http_client import BillingAPIClient
from libs.Payments import PaymentManager
from libs.Metering import MeteringManager
from libs.Credit import CreditManager
from libs.Contract import ContractManager
from libs.Batch import BatchManager
from libs.calculation import CalculationManager
from libs.adjustment import AdjustmentManager


@dataclass
class TestContext:
    """Container for test context and common objects."""
    
    env: str
    member: str
    month: str
    uuid: str
    config: InitializeConfig
    
    # Managers (lazy loaded)
    _payment_manager: Optional[PaymentManager] = None
    _metering_manager: Optional[MeteringManager] = None
    _credit_manager: Optional[CreditManager] = None
    _contract_manager: Optional[ContractManager] = None
    _batch_manager: Optional[BatchManager] = None
    _calculation_manager: Optional[CalculationManager] = None
    _adjustment_manager: Optional[AdjustmentManager] = None
    
    # Test data
    test_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def payment_manager(self) -> PaymentManager:
        """Get or create payment manager."""
        if self._payment_manager is None:
            self._payment_manager = PaymentManager(self.month, self.uuid)
        return self._payment_manager
    
    @property
    def metering_manager(self) -> MeteringManager:
        """Get or create metering manager."""
        if self._metering_manager is None:
            self._metering_manager = MeteringManager(self.month)
            if hasattr(self.config, 'appkey') and self.config.appkey:
                self._metering_manager.appkey = self.config.appkey[0]
        return self._metering_manager
    
    @property
    def credit_manager(self) -> CreditManager:
        """Get or create credit manager."""
        if self._credit_manager is None:
            self._credit_manager = CreditManager(self.uuid)
            if hasattr(self.config, 'campaign_id'):
                self._credit_manager.campaign_id = self.config.campaign_id
                self._credit_manager.give_campaign_id = getattr(self.config, 'give_campaign_id', None)
                self._credit_manager.paid_campaign_id = getattr(self.config, 'paid_campaign_id', None)
        return self._credit_manager
    
    @property
    def contract_manager(self) -> Optional[ContractManager]:
        """Get or create contract manager."""
        if self._contract_manager is None and hasattr(self.config, 'billing_group_id'):
            if self.config.billing_group_id:
                self._contract_manager = ContractManager(self.month, self.config.billing_group_id)
        return self._contract_manager
    
    @property
    def batch_manager(self) -> BatchManager:
        """Get or create batch manager."""
        if self._batch_manager is None:
            self._batch_manager = BatchManager(self.month)
            self._batch_manager.uuid = self.uuid
        return self._batch_manager
    
    @property
    def calculation_manager(self) -> CalculationManager:
        """Get or create calculation manager."""
        if self._calculation_manager is None:
            self._calculation_manager = CalculationManager(self.month, self.uuid)
        return self._calculation_manager
    
    @property
    def adjustment_manager(self) -> AdjustmentManager:
        """Get or create adjustment manager."""
        if self._adjustment_manager is None:
            self._adjustment_manager = AdjustmentManager(self.month)
        return self._adjustment_manager


class EnhancedBaseBillingTest:
    """Enhanced base class with common test functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_test_context(self, env: str, member: str, month: str) -> TestContext:
        """Set up test context automatically for each test."""
        # Generate unique UUID
        test_uuid = f"TEST_{uuid.uuid4().hex[:8]}"
        
        # Create config
        config = InitializeConfig(env, member, month)
        config.uuid = test_uuid
        
        # Clean data
        config.clean_data()
        config.before_test()
        
        # Create context
        self.context = TestContext(
            env=env,
            member=member,
            month=month,
            uuid=test_uuid,
            config=config
        )
        
        # Configure DI if needed
        if hasattr(self, 'use_dependency_injection') and self.use_dependency_injection:
            configure_dependencies(use_mock=False)
        
        yield self.context
        
        # Cleanup
        self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up after test."""
        try:
            # Cancel any credits
            if self.context._credit_manager:
                self.context.credit_manager.cancel_credit()
            
            # Clean data
            self.context.config.clean_data()
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    # Common test helpers
    def send_metering_data(
        self,
        counter_name: str = "cpu.usage",
        counter_type: str = "DELTA",
        counter_volume: float = 100,
        counter_unit: str = "n",
        resource_name: str = "test-resource"
    ) -> None:
        """Send metering data with defaults."""
        self.context.metering_manager.send_iaas_metering(
            counter_name=counter_name,
            counter_type=counter_type,
            counter_volume=counter_volume,
            counter_unit=counter_unit,
            resource_name=resource_name
        )
    
    def send_bulk_metering(self, count: int = 10, base_volume: float = 100) -> None:
        """Send multiple metering records."""
        for i in range(count):
            self.send_metering_data(
                counter_name=f"test.meter.{i}",
                counter_volume=base_volume + i
            )
    
    def perform_calculation(self, wait_for_stable: bool = True) -> Dict[str, Any]:
        """Perform billing calculation."""
        self.context.calculation_manager.send_billing_calc()
        
        if wait_for_stable:
            self.context.calculation_manager.wait_seconds_bill_stable()
        
        return self.context.calculation_manager.get_calculation_result()
    
    def setup_credit(self, amount: int = 10000, credit_type: str = "FREE") -> str:
        """Set up credit and return credit ID."""
        return self.context.credit_manager.give_credit(
            amount=amount,
            credit_type=credit_type
        )
    
    def create_contract(
        self,
        contract_type: str = "VOLUME",
        discount_rate: float = 10.0
    ) -> Dict[str, Any]:
        """Create a discount contract."""
        if not self.context.contract_manager:
            pytest.skip("Contract manager not available")
        
        return self.context.contract_manager.create_contract(
            contract_type=contract_type,
            discount_rate=discount_rate
        )
    
    def verify_payment_status(self, expected_status: str = "REGISTERED") -> None:
        """Verify payment status matches expected."""
        payment_id, status = self.context.payment_manager.get_payment_status()
        assert status == expected_status, f"Expected {expected_status}, got {status}"
    
    def verify_billing_amount(
        self,
        expected_amount: float,
        tolerance: float = 0.01
    ) -> None:
        """Verify billing amount within tolerance."""
        result = self.context.calculation_manager.get_calculation_result()
        actual_amount = result.get("totalAmount", 0)
        
        assert abs(actual_amount - expected_amount) < tolerance, \
            f"Expected {expected_amount}, got {actual_amount}"
    
    def run_batch_job(self, job_code: str) -> Dict[str, Any]:
        """Run a batch job and return result."""
        return self.context.batch_manager.request_batch_job(job_code)
    
    def apply_adjustment(
        self,
        adjustment_type: str,
        amount: float,
        reason: str = "Test adjustment"
    ) -> Dict[str, Any]:
        """Apply an adjustment."""
        return self.context.adjustment_manager.create_adjustment(
            adjustment_type=adjustment_type,
            amount=amount,
            reason=reason
        )


class ParameterizedTestMixin:
    """Mixin for parameterized test scenarios."""
    
    @pytest.fixture(params=[
        {"counter_type": "DELTA", "volume": 100},
        {"counter_type": "GAUGE", "volume": 200},
        {"counter_type": "CUMULATIVE", "volume": 300}
    ])
    def metering_params(self, request):
        """Parameterized metering data."""
        return request.param
    
    @pytest.fixture(params=["FREE", "PAID"])
    def credit_type(self, request):
        """Parameterized credit types."""
        return request.param
    
    @pytest.fixture(params=["REGISTERED", "READY", "PAID"])
    def payment_status(self, request):
        """Parameterized payment statuses."""
        return request.param
    
    @pytest.fixture(params=[
        {"type": "VOLUME", "rate": 10},
        {"type": "PERIOD", "rate": 20},
        {"type": "COMMITMENT", "rate": 15}
    ])
    def contract_params(self, request):
        """Parameterized contract configurations."""
        return request.param


class MockDataMixin:
    """Mixin for consistent mock data generation."""
    
    def generate_metering_data(self, count: int = 1) -> List[Dict[str, Any]]:
        """Generate consistent metering data."""
        return [
            {
                "counterName": f"test.counter.{i}",
                "counterType": "DELTA",
                "counterUnit": "n",
                "counterVolume": 100 + i * 10,
                "resourceId": f"resource-{uuid.uuid4().hex[:8]}",
                "resourceName": f"Test Resource {i}",
                "projectId": "test-project",
                "serviceName": "compute"
            }
            for i in range(count)
        ]
    
    def generate_payment_data(self) -> Dict[str, Any]:
        """Generate consistent payment data."""
        return {
            "paymentGroupId": f"pg-{uuid.uuid4().hex[:8]}",
            "amount": 10000,
            "currency": "KRW",
            "paymentMethod": "CREDIT_CARD",
            "paymentStatus": "READY"
        }
    
    def generate_credit_data(self, credit_type: str = "FREE") -> Dict[str, Any]:
        """Generate consistent credit data."""
        return {
            "campaignId": f"campaign-{uuid.uuid4().hex[:8]}",
            "creditType": credit_type,
            "amount": 50000,
            "expiryDate": "2024-12-31",
            "description": "Test credit"
        }
    
    def generate_contract_data(self) -> Dict[str, Any]:
        """Generate consistent contract data."""
        return {
            "contractId": f"contract-{uuid.uuid4().hex[:8]}",
            "contractType": "VOLUME",
            "discountRate": 10.0,
            "minimumCommitment": 100000,
            "startDate": "2024-01-01",
            "endDate": "2024-12-31"
        }
