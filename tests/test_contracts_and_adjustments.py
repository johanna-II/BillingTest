import logging
import math

import pytest

import libs.Calculation as calc
from libs.Adjustment import AdjustmentManager
from libs.constants import AdjustmentTarget
from libs.Contract import ContractManager as Contract
from libs.InitializeConfig import InitializeConfig
from libs.Metering import MeteringManager as Metering


def future_deprecated(func):
    def wrapper(*args):
        logging.warning(
            "주의: 이 테스트에서 사용하는 상품은 기간이 정해진 약정이므로 기간 종료 시 테스트 실패할 수 있습니다."
        )
        return func(*args)

    return wrapper


class TestNoContracts:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = InitializeConfig(env, member, month)

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = InitializeConfig(env, member, month)
        self.config.prepare()  # to change paymentStatus as REGISTERED
        self.contractObj = Contract(self.config.month, self.config.billing_group_id[0])
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="storage.volume.ssd",
            counter_type="DELTA",
            counter_unit="KB",
            counter_volume="524288000",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="network.floating_ip",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        self.contractObj.delete_contract()
        adjObj = AdjustmentManager(self.config.month)
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="Project", projectId=self.config.project_id[0]
        )
        if adjlist.get("adjustments"):
            adjObj.delete_adjustment(adjlist["adjustments"], AdjustmentTarget.PROJECT)
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
        )
        if adjlist.get("adjustments"):
            adjObj.delete_adjustment(
                adjlist["adjustments"], AdjustmentTarget.BILLING_GROUP
            )

    # 약정 없음, 프로젝트 고정할인+고정할증, 빌링그룹 고정할인+고정할증
    @future_deprecated
    def test_contadjTC1(self):
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )

        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        expected_result = (
            statements["charge"] - 1000 + 2000 - 1000 + 2000
        ) + math.floor((statements["charge"] - 1000 + 2000 - 1000 + 2000) * 0.1)
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_result,
        )

    # 약정 없음, 프로젝트 퍼센트할인+고정할증, 빌링그룹 고정할인+고정할증
    @future_deprecated
    def test_contadjTC2(self):
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )

        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        statements_no_vat = (
            statements["charge"]
            - math.ceil((statements["charge"] + 2000) * 0.1)
            + 2000
            - 1000
            + 2000
        )
        expected_result = statements_no_vat + math.floor(statements_no_vat * 0.1)
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_result,
        )

    # 약정 없음, 프로젝트 고정할인+고정할증, 빌링그룹 퍼센트할인+고정할증
    @future_deprecated
    def test_contadjTC3(self):
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=20,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )

        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        statements_no_vat = (
            (statements["charge"] - 1000 + 2000)
            - math.ceil((statements["charge"] - 1000 + 2000 + 2000) * 0.2)
            + 2000
        )
        expected_result = statements_no_vat + math.floor(statements_no_vat * 0.1)
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_result,
        )

    # 약정 없음, 프로젝트 퍼센트할인+고정할증, 빌링그룹 퍼센트할인+고정할증
    @future_deprecated
    def test_contadjTC4(self):
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=20,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )

        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        project_stats = (
            statements["charge"] - math.ceil((statements["charge"] + 2000) * 0.1) + 2000
        )
        total_stats_no_vat = (
            project_stats - math.ceil((project_stats + 2000) * 0.2) + 2000
        )
        total_statements = total_stats_no_vat + math.floor(total_stats_no_vat * 0.1)
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=total_statements,
        )


class TestPeriodContract:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = InitializeConfig(env, member, month)

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = InitializeConfig(env, member, month)
        self.config.prepare()  # to change paymentStatus as REGISTERED
        self.contractObj = Contract(self.config.month, self.config.billing_group_id[0])

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        self.contractObj.delete_contract()
        # self.config.clean_metering() - 더 이상 필요하지 않습니다
        adjObj = AdjustmentManager(self.config.month)
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="Project", projectId=self.config.project_id[0]
        )
        if adjlist.get("adjustments"):
            adjObj.delete_adjustment(adjlist["adjustments"], AdjustmentTarget.PROJECT)
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
        )
        if adjlist.get("adjustments"):
            adjObj.delete_adjustment(
                adjlist["adjustments"], AdjustmentTarget.BILLING_GROUP
            )

    @future_deprecated
    def test_contadjTC5(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="storage.volume.ssd",
            counter_type="DELTA",
            counter_unit="KB",
            counter_volume="524288000",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="network.floating_ip",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )

        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=1395561,
        )

    @future_deprecated
    def test_contadjTC6(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )

        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )

    @future_deprecated
    def test_contadjTC7(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="storage.volume.ssd",
            counter_type="DELTA",
            counter_unit="KB",
            counter_volume="524288000",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="network.floating_ip",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=50,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )

        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=698055,
        )

    @future_deprecated
    def test_contadjTC8(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=20,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )

        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )


class TestVolumeContract:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = InitializeConfig(env, member, month)

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = InitializeConfig(env, member, month)
        self.config.prepare()  # to change paymentStatus as REGISTERED
        self.contractObj = Contract(self.config.month, self.config.billing_group_id[0])

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        self.contractObj.delete_contract()
        # self.config.clean_metering() - 더 이상 필요하지 않습니다
        adjObj = AdjustmentManager(self.config.month)
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="Project", projectId=self.config.project_id[0]
        )
        if adjlist.get("adjustments"):
            adjObj.delete_adjustment(adjlist["adjustments"], AdjustmentTarget.PROJECT)
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
        )
        if adjlist.get("adjustments"):
            adjObj.delete_adjustment(
                adjlist["adjustments"], AdjustmentTarget.BILLING_GROUP
            )

    @future_deprecated
    def test_contadjTC9(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )

    @future_deprecated
    def test_contadjTC10(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="storage.volume.ssd",
            counter_type="DELTA",
            counter_unit="KB",
            counter_volume="524288000",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="network.floating_ip",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=1257269,
        )

    @future_deprecated
    def test_contadjTC11(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=50,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )

    @future_deprecated
    def test_contadjTC12(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="storage.volume.ssd",
            counter_type="DELTA",
            counter_unit="KB",
            counter_volume="524288000",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="network.floating_ip",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=20,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=1006254,
        )


class TestPartnerContract:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = InitializeConfig(env, member, month)
        # self.config.clean_data() - 더 이상 필요하지 않습니다

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = InitializeConfig(env, member, month)
        self.config.prepare()  # to change paymentStatus as REGISTERED
        self.contractObj = Contract(self.config.month, self.config.billing_group_id[0])

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        self.contractObj.delete_contract()
        # self.config.clean_metering() - 더 이상 필요하지 않습니다
        adjObj = AdjustmentManager(self.config.month)
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="Project", projectId=self.config.project_id[0]
        )
        if adjlist.get("adjustments"):
            adjObj.delete_adjustment(adjlist["adjustments"], AdjustmentTarget.PROJECT)
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
        )
        if adjlist.get("adjustments"):
            adjObj.delete_adjustment(
                adjlist["adjustments"], AdjustmentTarget.BILLING_GROUP
            )

    @future_deprecated
    def test_contadjTC13(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="storage.volume.ssd",
            counter_type="DELTA",
            counter_unit="KB",
            counter_volume="524288000",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="network.floating_ip",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=1385661,
        )

    @future_deprecated
    def test_contadjTC14(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )

    @future_deprecated
    def test_contadjTC15(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=50,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )

    @future_deprecated
    def test_contadjTC16(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.apply_contract()
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="storage.volume.ssd",
            counter_type="DELTA",
            counter_unit="KB",
            counter_volume="524288000",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="network.floating_ip",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
        )
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )
        adjObj = AdjustmentManager(self.config.month)
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=20,
        )
        adjObj.apply_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc(self.config.month, self.config.uuid)
        calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        self.config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=999126,
        )
