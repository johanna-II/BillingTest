from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta

import libs.Calculation as calc
from libs.Adjustment import AdjustmentManager
from libs.Batch import BatchManager as Batches
from libs.Contract import ContractManager as Contract
from libs.Credit import CreditManager as Credit
from libs.InitializeConfig import InitializeConfig
from libs.Metering import MeteringManager as Metering
from libs.Payments import PaymentManager as Payments


@pytest.mark.core
@pytest.mark.credit
@pytest.mark.billing
@pytest.mark.integration
@pytest.mark.mock_required
class TestUnpaidWithCredit:
    @pytest.fixture(autouse=True)
    def setup(self, env, member, month) -> None:
        if member == "etc":
            pytest.skip(
                "Credit test should be skipped if member country is not KR or JP"
            )
        self.config = InitializeConfig(env, member, month)
        self.config.prepare()
        self.clean_all_month_resources()
        self.config.month = self.calc_prev_month(month=2)
        # 전전월 미터링 전송
        self.send_prev_month_metering(month=2)
        # 전전월 결제 상태 변경 (REGISTERED -> READY)
        self.send_payments_change(month=2)
        # 연체료 배치 (연체료 - 전월 기준)
        self.send_batch_request(month=1)
        # 전월/당월 미터링 전송
        self.send_prev_month_metering(month=1)
        # 전월 결제 완료
        self.send_payments_change(month=1)
        self.payment_prev_month(month=1)
        self.credit = Credit()
        self.credit.uuid = self.config.uuid
        self.credit.campaign_id = self.config.campaign_id
        self.credit.give_campaign_id = self.config.give_campaign_id
        self.credit.paid_campaign_id = self.config.paid_campaign_id

    @pytest.fixture(autouse=True)
    def teardown(self):
        yield
        self.send_payments_change(month=2)
        self.send_payments_change(month=0)
        self.credit.cancel_credit()
        adjObj = AdjustmentManager(self.config.month)
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="Project", projectId=self.config.project_id[0]
        )
        adjObj.delete_adjustment(adjlist)
        adjlist = adjObj.inquiry_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupid=self.config.billing_group_id[0],
        )
        adjObj.delete_adjustment(adjlist)
        contractObj = Contract(self.config.month, self.config.billing_group_id[0])
        contractObj.delete_contract()

    def test_unpaid_and_credit_TC1(self) -> None:
        self.config.month = self.calc_prev_month(month=0)
        self.send_prev_month_metering(month=0)
        contractObj = Contract(self.config.month, self.config.billing_group_id[0])
        contractObj.apply_contract(contract_id="<contractID>")
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
            adjustmentType="FIXED_SURCHARGE",
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
            adjustmentType="FIXED_SURCHARGE",
            adjustment=2000,
        )
        # self.credit.giveCredit("JmqOU3ilVhppkmUM", 2000000)  # 2,000,000 / 무료, 지급형, 이벤트 크레딧
        self.credit.give_credit("<creditCode>")
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculation_all()

        # 전전월 결제 및 영수증 발행
        self.config.month = self.calc_prev_month(month=2)
        prev_statements, prev_total_payments = self.config.common_test()
        prev_total_statements = (
            prev_statements["totalAmount"] - prev_statements["totalCredit"]
        )
        prev_rest_credit, prev_total_credit_amt = self.credit.inquiry_rest_credit()

        # 전전월 계산 후 결제 금액 및 매출 전표 값 비교 assertion
        self.config.verify_assert(
            statements=prev_total_statements,
            payments=prev_total_payments,
            expected_result=1324049,
            rest_credit=prev_rest_credit,
            total_credit=prev_total_credit_amt,
            expected_credit=1815888,
        )

        # 당월 결제 및 영수증 발행
        self.config.month = self.calc_prev_month(month=0)
        statements, total_payments = self.config.common_test()
        total_statements = statements["totalAmount"] - statements["totalCredit"]
        rest_credit, total_credit_amt = self.credit.inquiry_rest_credit()

        # 당월 계산 후 결제 금액 및 매출 전표 값 비교 assertion
        self.config.verify_assert(
            statements=total_statements,
            payments=total_payments,
            expected_result=1171359,
        )
        self.config.verify_assert(
            rest_credit=rest_credit,
            total_credit=total_credit_amt,
            expected_credit=1649776,
        )

    def test_unpaid_and_credit_TC2(self) -> None:
        self.send_prev_month_metering(month=0)
        self.config.month = self.calc_prev_month(month=0)
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
            adjustmentType="FIXED_SURCHARGE",
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
            adjustmentType="FIXED_SURCHARGE",
            adjustment=2000,
        )
        self.credit.give_credit(
            "<creditCode>", 2000000
        )  # 2,000,000 / 무료, 지급형, 이벤트 크레딧
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculation_all()

        # 전전월 결제 및 영수증 발행
        self.config.month = self.calc_prev_month(month=2)
        prev_statements, prev_total_payments = self.config.common_test()
        prev_total_statements = (
            prev_statements["totalAmount"] - prev_statements["totalCredit"]
        )
        prev_rest_credit, prev_total_credit_amt = self.credit.inquiry_rest_credit()

        # 전전월 계산 후 결제 금액 및 매출 전표 값 비교 assertion
        self.config.verify_assert(
            statements=prev_total_statements,
            payments=prev_total_payments,
            expected_result=1324049,
        )
        self.config.verify_assert(
            rest_credit=prev_rest_credit,
            total_credit=prev_total_credit_amt,
            expected_credit=1815888,
        )

        # 당월 결제 및 영수증 발행
        self.config.month = self.calc_prev_month(month=0)
        statements, total_payments = self.config.common_test()
        total_statements = statements["totalAmount"] - statements["totalCredit"]
        prev_rest_credit, prev_total_credit_amt = self.credit.inquiry_rest_credit()

        # 당월 계산 후 결제 금액 및 매출 전표 값 비교 assertion
        self.config.verify_assert(
            statements=total_statements,
            payments=total_payments,
            expected_result=1171359,
        )
        self.config.verify_assert(
            rest_credit=prev_rest_credit,
            total_credit=prev_total_credit_amt,
            expected_credit=1631776,
        )

    @staticmethod
    def calc_prev_month(month):
        prev_month = datetime.now() - relativedelta(months=month)
        year, month = prev_month.year, prev_month.month
        month = (
            "0" + prev_month.month.__str__()
            if prev_month.month < 10
            else prev_month.month
        )
        return year.__str__() + "-" + month.__str__()

    def send_prev_month_metering(self, month) -> None:
        month = self.calc_prev_month(month=month)
        meteringObj = Metering(month)
        meteringObj.month = self.config.month = month
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
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculation_all()

    def send_payments_change(self, month) -> None:
        month = self.calc_prev_month(month=month)
        paymentsObj = Payments(month)
        paymentsObj.month = self.config.month = month
        paymentsObj.uuid = self.config.uuid
        pgId, pgStatusCode = paymentsObj.inquiry_payment()
        if pgStatusCode == "PAID":
            paymentsObj.cancel_payment(pgId)
        elif pgStatusCode == "REGISTERED":
            paymentsObj.change_payment(pgId)
        else:
            pass

    def send_batch_request(self, month) -> None:
        month = self.calc_prev_month(month=month)
        batchObj = Batches(month)
        batchObj.month = self.config.month = month
        batchObj.batch_job_code = "CALC_LATE_FEE"
        batchObj.send_batch_request()

    def clean_all_month_resources(self) -> None:
        # 모든 월 초기화 처리
        for idx in range(3):
            month = self.calc_prev_month(month=idx)
            self.config.month = month
            self.config.clean_data()

    def compare_unpaid(self):
        prev_month = self.calc_prev_month(month=1)
        paymentsObj = Payments(prev_month)
        paymentsObj.uuid = self.config.uuid
        prev_unpaid = paymentsObj.unpaid()
        cur_month = self.calc_prev_month(month=0)
        paymentsObj = Payments(cur_month)
        paymentsObj.uuid = self.config.uuid
        cur_unpaid = paymentsObj.unpaid()
        return prev_unpaid, cur_unpaid

    def payment_prev_month(self, month) -> None:
        month = self.calc_prev_month(month=month)
        paymentsObj = Payments(month)
        paymentsObj.month = self.config.month = month
        paymentsObj.uuid = self.config.uuid
        pgId, pgStatusCode = paymentsObj.inquiry_payment()
        if pgStatusCode == "PAID":
            paymentsObj.cancel_payment(pgId)
        elif pgStatusCode == "REGISTERED":
            paymentsObj.change_payment(pgId)
        else:
            pass
        paymentsObj.payment(pgId)
