import pytest
import libs.InitializeConfig as creditutil
import libs.Metering as metering
import libs.Payments as payments
import libs.Batch as batch
import libs.Calculation as calc
import libs.Credit as credit
import libs.Adjustment as adj
import libs.Contract as contract
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TestUnpaidWithCredit:
    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        if member == "etc":
            pytest.skip("Credit test should be skipped if member country is not KR or JP")
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.beforeTest()
        self.cleanAllMonthResources()
        self.config.month = self.calcPrevMonth(month=2)
        # 전전월 미터링 전송
        self.sendPrevMonthMetering(month=2)
        # 전전월 결제 상태 변경 (REGISTERED -> READY)
        self.sendPaymentsChange(month=2)
        # 연체료 배치 (연체료 - 전월 기준)
        self.sendBatchRequest(month=1)
        # 전월/당월 미터링 전송
        self.sendPrevMonthMetering(month=1)
        # 전월 결제 완료
        self.sendPaymentsChange(month=1)
        self.paymentPrevMonth(month=1)
        self.credit = credit.Credit()
        self.credit.uuid = self.config.uuid
        self.credit.campaign_id = self.config.campaign_id
        self.credit.give_campaign_id = self.config.give_campaign_id
        self.credit.paid_campaign_id = self.config.paid_campaign_id

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self):
        yield
        self.sendPaymentsChange(month=2)
        self.sendPaymentsChange(month=0)
        self.credit.cancelCredit()
        adjObj = adj.Adjustments(self.config.month)
        adjlist = adjObj.inquiryAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0])
        adjObj.deleteAdjustment(adjlist)
        adjlist = adjObj.inquiryAdjustment(adjustmentTarget="BillingGroup", billingGroupid=self.config.billing_group_id[0])
        adjObj.deleteAdjustment(adjlist)
        contractObj = contract.Contract(self.config.month, self.config.billing_group_id[0])
        contractObj.deleteContract()

    def test_unpaid_and_credit_TC1(self):
        self.config.month = self.calcPrevMonth(month=0)
        self.sendPrevMonthMetering(month=0)
        contractObj = contract.Contract(self.config.month, self.config.billing_group_id[0])
        contractObj.contractId = "<contractID>"
        contractObj.applyContract()
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="PERCENT_DISCOUNT", adjustment=10)
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="STATIC_EXTRA", adjustment=2000)
        adjObj.applyAdjustment(adjustmentTarget="BillingGroup", billingGroupId=self.config.billing_group_id[0],
                               adjustmentType="STATIC_DISCOUNT", adjustment=1000)
        adjObj.applyAdjustment(adjustmentTarget="BillingGroup", billingGroupId=self.config.billing_group_id[0],
                               adjustmentType="STATIC_EXTRA", adjustment=2000)
        # self.credit.giveCredit("JmqOU3ilVhppkmUM", 2000000)  # 2,000,000 / 무료, 지급형, 이벤트 크레딧
        self.credit.giveCredit("<creditCode>")
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()

        # 전전월 결제 및 영수증 발행
        self.config.month = self.calcPrevMonth(month=2)
        prev_statements, prev_total_payments = self.config.commonTest()
        prev_total_statements = prev_statements['totalAmount'] - prev_statements['totalCredit']
        prev_rest_credit, prev_total_credit_amt = self.credit.inquiryRestCredit()

        # 전전월 계산 후 결제 금액 및 매출 전표 값 비교 assertion
        self.config.verifyAssert(statements=prev_total_statements, payments=prev_total_payments,
                                 expected_result=1324049,
                                 rest_credit=prev_rest_credit, total_credit=prev_total_credit_amt,
                                 expected_credit=1815888)

        # 당월 결제 및 영수증 발행
        self.config.month = self.calcPrevMonth(month=0)
        statements, total_payments = self.config.commonTest()
        total_statements = statements['totalAmount'] - statements['totalCredit']
        rest_credit, total_credit_amt = self.credit.inquiryRestCredit()

        # 당월 계산 후 결제 금액 및 매출 전표 값 비교 assertion
        self.config.verifyAssert(statements=total_statements, payments=total_payments, expected_result=1171359)
        self.config.verifyAssert(rest_credit=rest_credit, total_credit=total_credit_amt,
                                 expected_credit=1649776)

    def test_unpaid_and_credit_TC2(self):
        self.sendPrevMonthMetering(month=0)
        self.config.month = self.calcPrevMonth(month=0)
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="PERCENT_DISCOUNT", adjustment=10)
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="STATIC_EXTRA", adjustment=2000)
        adjObj.applyAdjustment(adjustmentTarget="BillingGroup", billingGroupId=self.config.billing_group_id[0],
                               adjustmentType="STATIC_DISCOUNT", adjustment=1000)
        adjObj.applyAdjustment(adjustmentTarget="BillingGroup", billingGroupId=self.config.billing_group_id[0],
                               adjustmentType="STATIC_EXTRA", adjustment=2000)
        self.credit.giveCredit("<creditCode>", 2000000)  # 2,000,000 / 무료, 지급형, 이벤트 크레딧
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()

        # 전전월 결제 및 영수증 발행
        self.config.month = self.calcPrevMonth(month=2)
        prev_statements, prev_total_payments = self.config.commonTest()
        prev_total_statements = prev_statements['totalAmount'] - prev_statements['totalCredit']
        prev_rest_credit, prev_total_credit_amt = self.credit.inquiryRestCredit()

        # 전전월 계산 후 결제 금액 및 매출 전표 값 비교 assertion
        self.config.verifyAssert(statements=prev_total_statements, payments=prev_total_payments, expected_result=1324049)
        self.config.verifyAssert(rest_credit=prev_rest_credit, total_credit=prev_total_credit_amt, expected_credit=1815888)

        # 당월 결제 및 영수증 발행
        self.config.month = self.calcPrevMonth(month=0)
        statements, total_payments = self.config.commonTest()
        total_statements = statements['totalAmount'] - statements['totalCredit']
        prev_rest_credit, prev_total_credit_amt = self.credit.inquiryRestCredit()

        # 당월 계산 후 결제 금액 및 매출 전표 값 비교 assertion
        self.config.verifyAssert(statements=total_statements, payments=total_payments, expected_result=1171359)
        self.config.verifyAssert(rest_credit=prev_rest_credit, total_credit=prev_total_credit_amt, expected_credit=1631776)

    @staticmethod
    def calcPrevMonth(month):
        prev_month = datetime.now() - relativedelta(months=month)
        year, month = prev_month.year, prev_month.month
        month = "0" + prev_month.month.__str__() if prev_month.month < 10 else prev_month.month
        month_return = year.__str__() + "-" + month.__str__()
        print(f"+ 전전월/전월 계산 {month_return}")
        return month_return

    def sendPrevMonthMetering(self, month):
        month = self.calcPrevMonth(month=month)
        meteringObj = metering.Metering(month)
        meteringObj.month = self.config.month = month
        meteringObj.appkey = self.config.appkey[0]
        meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        meteringObj.sendIaaSMetering(counterName="storage.volume.ssd", counterType="DELTA", counterUnit="KB", counterVolume="524288000")
        meteringObj.sendIaaSMetering(counterName="network.floating_ip", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        meteringObj.sendIaaSMetering(counterName="compute.g2.t4.c8m64", counterType="GAUGE", counterUnit="HOURS", counterVolume="720")
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()

    def sendPaymentsChange(self, month):
        month = self.calcPrevMonth(month=month)
        paymentsObj = payments.Payments(month)
        paymentsObj.month = self.config.month = month
        paymentsObj.uuid = self.config.uuid
        pgId, pgStatusCode = paymentsObj.inquiryPayment()
        if pgStatusCode == "PAID":
            paymentsObj.cancelPayment(pgId)
        elif pgStatusCode == "REGISTERED":
            paymentsObj.changePayment(pgId)
        else:
            print("++ 결제 상태 : READY, skipped change status")

    def sendBatchRequest(self, month):
        month = self.calcPrevMonth(month=month)
        batchObj = batch.Batches(month)
        batchObj.month = self.config.month = month
        batchObj.batchJobCode = "CALC_LATE_FEE"
        batchObj.sendBatchRequest()

    def cleanAllMonthResources(self):
        # 모든 월 초기화 처리
        for idx in range(3):
            month = self.calcPrevMonth(month=idx)
            self.config.month = month
            self.config.cleanData()

    def compareUnpaid(self):
        prev_month = self.calcPrevMonth(month=1)
        paymentsObj = payments.Payments(prev_month)
        paymentsObj.uuid = self.config.uuid
        prev_unpaid = paymentsObj.unpaid()
        cur_month = self.calcPrevMonth(month=0)
        paymentsObj = payments.Payments(cur_month)
        paymentsObj.uuid = self.config.uuid
        cur_unpaid = paymentsObj.unpaid()
        print(f'{prev_month}월 미납 금액: {prev_unpaid}, {cur_month}월 미납 금액: {cur_unpaid}')
        return prev_unpaid, cur_unpaid

    def paymentPrevMonth(self, month):
        month = self.calcPrevMonth(month=month)
        paymentsObj = payments.Payments(month)
        paymentsObj.month = self.config.month = month
        paymentsObj.uuid = self.config.uuid
        pgId, pgStatusCode = paymentsObj.inquiryPayment()
        if pgStatusCode == "PAID":
            paymentsObj.cancelPayment(pgId)
        elif pgStatusCode == "REGISTERED":
            paymentsObj.changePayment(pgId)
        else:
            print("++ 결제 상태 : READY, skipped change status")
        paymentsObj.payment(pgId)
