import pytest
import libs.InitializeConfig as creditutil
import libs.Metering as metering
import libs.Contract as contract
import libs.Calculation as calc
import libs.Adjustment as adj
import math
import logging


def futureDeprecated(func):
    def wrapper(*args):
        logging.warning(
            "주의: 이 테스트에서 사용하는 상품은 기간이 정해진 약정이므로 기간 종료 시 테스트 실패할 수 있습니다."
        )
        return func(*args)

    return wrapper


class TestNoContracts:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.cleanData()

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.beforeTest()  # to change paymentStatus as REGISTERED
        self.contractObj = contract.Contract(
            self.config.month, self.config.billing_group_id[0]
        )
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="720",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="storage.volume.ssd",
            counterType="DELTA",
            counterUnit="KB",
            counterVolume="524288000",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="network.floating_ip",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="720",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="compute.g2.t4.c8m64",
            counterType="GAUGE",
            counterUnit="HOURS",
            counterVolume="720",
        )

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        self.contractObj.deleteContract()
        adjObj = adj.Adjustments(self.config.month)
        adjlist = adjObj.inquiryAdjustment(
            adjustmentTarget="Project", projectId=self.config.project_id[0]
        )
        adjObj.deleteAdjustment(adjlist)
        adjlist = adjObj.inquiryAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupid=self.config.billing_group_id[0],
        )
        adjObj.deleteAdjustment(adjlist)

    # 약정 없음, 프로젝트 고정할인+고정할증, 빌링그룹 고정할인+고정할증
    @futureDeprecated
    def test_contadjTC1(self):
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )

        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        expected_result = (
            statements["charge"] - 1000 + 2000 - 1000 + 2000
        ) + math.floor((statements["charge"] - 1000 + 2000 - 1000 + 2000) * 0.1)
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_result,
        )

    # 약정 없음, 프로젝트 퍼센트할인+고정할증, 빌링그룹 고정할인+고정할증
    @futureDeprecated
    def test_contadjTC2(self):
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )

        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        statements_no_vat = (
            statements["charge"]
            - math.ceil((statements["charge"] + 2000) * 0.1)
            + 2000
            - 1000
            + 2000
        )
        expected_result = statements_no_vat + math.floor(statements_no_vat * 0.1)
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_result,
        )

    # 약정 없음, 프로젝트 고정할인+고정할증, 빌링그룹 퍼센트할인+고정할증
    @futureDeprecated
    def test_contadjTC3(self):
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=20,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )

        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        statements_no_vat = (
            (statements["charge"] - 1000 + 2000)
            - math.ceil((statements["charge"] - 1000 + 2000 + 2000) * 0.2)
            + 2000
        )
        expected_result = statements_no_vat + math.floor(statements_no_vat * 0.1)
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_result,
        )

    # 약정 없음, 프로젝트 퍼센트할인+고정할증, 빌링그룹 퍼센트할인+고정할증
    @futureDeprecated
    def test_contadjTC4(self):
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=20,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )

        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        project_stats = (
            statements["charge"] - math.ceil((statements["charge"] + 2000) * 0.1) + 2000
        )
        total_stats_no_vat = (
            project_stats - math.ceil((project_stats + 2000) * 0.2) + 2000
        )
        total_statements = total_stats_no_vat + math.floor(total_stats_no_vat * 0.1)
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=total_statements,
        )


class TestPeriodContract:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.cleanData()

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.beforeTest()  # to change paymentStatus as REGISTERED
        self.contractObj = contract.Contract(
            self.config.month, self.config.billing_group_id[0]
        )

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        self.contractObj.deleteContract()
        self.config.cleanMetering()
        adjObj = adj.Adjustments(self.config.month)
        adjlist = adjObj.inquiryAdjustment(
            adjustmentTarget="Project", projectId=self.config.project_id[0]
        )
        adjObj.deleteAdjustment(adjlist)
        adjlist = adjObj.inquiryAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupid=self.config.billing_group_id[0],
        )
        adjObj.deleteAdjustment(adjlist)

    @futureDeprecated
    def test_contadjTC5(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="storage.volume.ssd",
            counterType="DELTA",
            counterUnit="KB",
            counterVolume="524288000",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="network.floating_ip",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="720",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="compute.g2.t4.c8m64",
            counterType="GAUGE",
            counterUnit="HOURS",
            counterVolume="720",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )

        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=1395561,
        )

    @futureDeprecated
    def test_contadjTC6(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )

        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )

    @futureDeprecated
    def test_contadjTC7(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="storage.volume.ssd",
            counterType="DELTA",
            counterUnit="KB",
            counterVolume="524288000",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="network.floating_ip",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="720",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="compute.g2.t4.c8m64",
            counterType="GAUGE",
            counterUnit="HOURS",
            counterVolume="720",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=50,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )

        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=698055,
        )

    @futureDeprecated
    def test_contadjTC8(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=20,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )

        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )


class TestVolumeContract:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.cleanData()

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.beforeTest()  # to change paymentStatus as REGISTERED
        self.contractObj = contract.Contract(
            self.config.month, self.config.billing_group_id[0]
        )

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        self.contractObj.deleteContract()
        self.config.cleanMetering()
        adjObj = adj.Adjustments(self.config.month)
        adjlist = adjObj.inquiryAdjustment(
            adjustmentTarget="Project", projectId=self.config.project_id[0]
        )
        adjObj.deleteAdjustment(adjlist)
        adjlist = adjObj.inquiryAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupid=self.config.billing_group_id[0],
        )
        adjObj.deleteAdjustment(adjlist)

    @futureDeprecated
    def test_contadjTC9(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )

    @futureDeprecated
    def test_contadjTC10(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="storage.volume.ssd",
            counterType="DELTA",
            counterUnit="KB",
            counterVolume="524288000",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="network.floating_ip",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="720",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="compute.g2.t4.c8m64",
            counterType="GAUGE",
            counterUnit="HOURS",
            counterVolume="720",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=1257269,
        )

    @futureDeprecated
    def test_contadjTC11(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=50,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )

    @futureDeprecated
    def test_contadjTC12(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="storage.volume.ssd",
            counterType="DELTA",
            counterUnit="KB",
            counterVolume="524288000",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="network.floating_ip",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="720",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="compute.g2.t4.c8m64",
            counterType="GAUGE",
            counterUnit="HOURS",
            counterVolume="720",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=20,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=1006254,
        )


class TestPartnerContract:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.cleanData()

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.beforeTest()  # to change paymentStatus as REGISTERED
        self.contractObj = contract.Contract(
            self.config.month, self.config.billing_group_id[0]
        )

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        self.contractObj.deleteContract()
        self.config.cleanMetering()
        adjObj = adj.Adjustments(self.config.month)
        adjlist = adjObj.inquiryAdjustment(
            adjustmentTarget="Project", projectId=self.config.project_id[0]
        )
        adjObj.deleteAdjustment(adjlist)
        adjlist = adjObj.inquiryAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupid=self.config.billing_group_id[0],
        )
        adjObj.deleteAdjustment(adjlist)

    @futureDeprecated
    def test_contadjTC13(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="storage.volume.ssd",
            counterType="DELTA",
            counterUnit="KB",
            counterVolume="524288000",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="network.floating_ip",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="720",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="compute.g2.t4.c8m64",
            counterType="GAUGE",
            counterUnit="HOURS",
            counterVolume="720",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=1385661,
        )

    @futureDeprecated
    def test_contadjTC14(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=500,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )

    @futureDeprecated
    def test_contadjTC15(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_DISCOUNT",
            adjustment=1000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=50,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=110000,
        )

    @futureDeprecated
    def test_contadjTC16(self):
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(
            counterName="compute.c2.c8m8",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="360",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="storage.volume.ssd",
            counterType="DELTA",
            counterUnit="KB",
            counterVolume="524288000",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="network.floating_ip",
            counterType="DELTA",
            counterUnit="HOURS",
            counterVolume="720",
        )
        self.meteringObj.sendIaaSMetering(
            counterName="compute.g2.t4.c8m64",
            counterType="GAUGE",
            counterUnit="HOURS",
            counterVolume="720",
        )
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=10,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="Project",
            projectId=self.config.project_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=2000,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="PERCENT_DISCOUNT",
            adjustment=20,
        )
        adjObj.applyAdjustment(
            adjustmentTarget="BillingGroup",
            billingGroupId=self.config.billing_group_id[0],
            adjustmentType="STATIC_EXTRA",
            adjustment=3000,
        )
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        self.config.verifyAssert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=999126,
        )
