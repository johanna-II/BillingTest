import pytest
from libs.InitializeConfig import InitializeConfig
from libs.Metering import MeteringManager as Metering
from libs.Calculation import CalculationManager as Calculation
from libs.Adjustment import AdjustmentManager as Adjustments
import math
import os


@pytest.mark.core
@pytest.mark.adjustment
@pytest.mark.billing
@pytest.mark.integration
@pytest.mark.mock_required
class TestAdjustmentOnly:
    def _get_payment_and_verify(self, expected_charge_modifier=0, expected_rate_modifier=1.0):
        """Helper method to get payment statement and verify amounts"""
        payment_manager = self.config.payment_manager
        statement_result = payment_manager.get_payment_statement()
        statements = statement_result.get("statements", [{}])[0] if statement_result else {}
        
        # 기본 charge 계산
        base_charge = statements.get("charge", 241213)
        
        # Adjustment 적용
        if expected_rate_modifier != 1.0:
            # 퍼센트 할인/할증
            modified_charge = base_charge * expected_rate_modifier
        else:
            # 고정 금액 할인/할증
            modified_charge = base_charge + expected_charge_modifier
            
        # VAT 계산 (10%)
        vat = math.floor(modified_charge * 0.1)
        expected_total = int(modified_charge) + vat
        actual_total = statements.get("amount", 0)
        
        assert actual_total == expected_total, f"Expected {expected_total}, got {actual_total}"
        return statements, expected_total
    
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = InitializeConfig(env, member, month)
        meteringObj = Metering(month=self.config.month)
        # Use the first appkey from config
        app_key = self.config.appkey[0] if hasattr(self.config, 'appkey') and self.config.appkey else "test_app"
        
        meteringObj.send_metering(
            app_key=app_key,
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        meteringObj.send_metering(
            app_key=app_key,
            counter_name="storage.volume.ssd",
            counter_type="DELTA",
            counter_unit="KB",
            counter_volume="524288000",
        )
        meteringObj.send_metering(
            app_key=app_key,
            counter_name="network.floating_ip",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        meteringObj.send_metering(
            app_key=app_key,
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = InitializeConfig(env, member, month)
        self.config.prepare()  # to change paymentStatus as REGISTERED

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        adjObj = Adjustments(self.config.month)
        adjlist = adjObj.get_adjustments(
            adjustment_target="BillingGroup",
            target_id=self.config.billing_group_id[0],
        )
        adjObj.delete_adjustment(adjlist, adjustment_target="BillingGroup")

    # 빌링그룹 고정 할인
    def test_bgAdjTC1(self):
        adjObj = Adjustments(self.config.month)
        adjObj.apply_adjustment(
            adjustment_target="BillingGroup",
            target_id=self.config.billing_group_id[0],
            adjustment_type="STATIC_DISCOUNT",
            adjustment_amount=1000,
        )
        calcObj = Calculation(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교 - 1000원 할인
        self._get_payment_and_verify(expected_charge_modifier=-1000)

    # 빌링그룹 퍼센트 할인
    def test_bgAdjTC2(self):
        adjObj = Adjustments(self.config.month)
        adjObj.apply_adjustment(
            adjustment_target="BillingGroup",
            target_id=self.config.billing_group_id[0],
            adjustment_type="PERCENT_DISCOUNT",
            adjustment_amount=5,
        )
        calcObj = Calculation(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교 - 5% 할인
        self._get_payment_and_verify(expected_rate_modifier=0.95)

    # 빌링그룹 고정 할증
    def test_bgAdjTC3(self):
        adjObj = Adjustments(self.config.month)
        adjObj.apply_adjustment(
            adjustment_target="BillingGroup",
            target_id=self.config.billing_group_id[0],
            adjustment_type="STATIC_EXTRA",
            adjustment_amount=5000,
        )
        calcObj = Calculation(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교 - 5000원 할증
        self._get_payment_and_verify(expected_charge_modifier=5000)

    # 빌링그룹 고정 할인 + 고정 할증
    def test_bgAdjTC4(self):
        adjObj = Adjustments(self.config.month)
        adjObj.apply_adjustment(
            adjustment_target="BillingGroup",
            target_id=self.config.billing_group_id[0],
            adjustment_type="STATIC_DISCOUNT",
            adjustment_amount=100,
        )
        adjObj.apply_adjustment(
            adjustment_target="BillingGroup",
            target_id=self.config.billing_group_id[0],
            adjustment_type="STATIC_EXTRA",
            adjustment_amount=1000,
        )
        calcObj = Calculation(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교 - 1000원 할증, 100원 할인 = 실제로 900원 할증
        self._get_payment_and_verify(expected_charge_modifier=900)

    # 빌링그룹 퍼센트 할인 + 고정 할증
    def test_bgAdjTC5(self):
        adjObj = Adjustments(self.config.month)
        adjObj.apply_adjustment(
            adjustment_target="BillingGroup",
            target_id=self.config.billing_group_id[0],
            adjustment_type="PERCENT_DISCOUNT",
            adjustment_amount=10,
        )
        adjObj.apply_adjustment(
            adjustment_target="BillingGroup",
            target_id=self.config.billing_group_id[0],
            adjustment_type="STATIC_EXTRA",
            adjustment_amount=2000,
        )
        calcObj = Calculation(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        # 복잡한 계산: 먼저 2000원 할증, 그 다음 10% 할인 적용
        payment_manager = self.config.payment_manager
        statement_result = payment_manager.get_payment_statement()
        statements = statement_result.get("statements", [{}])[0] if statement_result else {}
        
        base_charge = statements.get("charge", 241213)
        # 1. 고정 할증 적용
        charge_with_extra = base_charge + 2000
        # 2. 퍼센트 할인 적용 (10%)
        final_charge = charge_with_extra * 0.9
        # 3. VAT 계산
        vat = math.floor(final_charge * 0.1)
        expected_total = int(final_charge) + vat
        actual_total = statements.get("amount", 0)
        
        assert actual_total == expected_total, f"Expected {expected_total}, got {actual_total}"
