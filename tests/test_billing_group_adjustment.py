import pytest
from libs import InitializeConfig
from libs import Metering
from libs import Calculation
from libs.adjustment import AdjustmentManager as Adjustments
import math


@pytest.mark.core
@pytest.mark.adjustment
@pytest.mark.billing
@pytest.mark.integration
@pytest.mark.mock_required
class TestAdjustmentOnly:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = InitializeConfig(env, member, month)
        self.config.clean_data()
        meteringObj = Metering(self.config.month)
        meteringObj.appkey = self.config.appkey[0]
        meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        meteringObj.send_iaas_metering(
            counter_name="storage.volume.ssd",
            counter_type="DELTA",
            counter_unit="KB",
            counter_volume="524288000",
        )
        meteringObj.send_iaas_metering(
            counter_name="network.floating_ip",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = InitializeConfig(env, member, month)
        self.config.before_test()  # to change paymentStatus as REGISTERED

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
        calcObj.recalculation_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        expect_result = (statements["charge"] - 1000) + math.floor(
            (statements["charge"] - 1000) * 0.1
        )
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expect_result,
        )

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
        calcObj.recalculation_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        percent_discounted = math.ceil(statements["charge"] * (5 * 0.01))
        expect_result = (statements["charge"] - percent_discounted) + math.floor(
            (statements["charge"] - percent_discounted) * 0.1
        )
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expect_result,
        )

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
        calcObj.recalculation_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        expect_result = (statements["charge"] + 5000) + math.floor(
            (statements["charge"] + 5000) * 0.1
        )
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expect_result,
        )

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
        calcObj.recalculation_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        originalCharge = statements["charge"] + 1000 - 100
        expect_result = originalCharge + math.floor(originalCharge * 0.1)
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expect_result,
        )

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
        calcObj.recalculation_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        originalCharge = (statements["charge"] + 2000) - math.ceil(
            (statements["charge"] + 2000) * 10 * 0.01
        )
        expect_result = originalCharge + math.floor(originalCharge * 0.1)
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expect_result,
        )
