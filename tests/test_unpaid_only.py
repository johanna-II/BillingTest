import pytest
import libs.InitializeConfig as creditutil
import libs.Metering as metering
import libs.Payments as payments
import libs.Batch as batch
import libs.Calculation as calc
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TestUnpaidOnly:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        # 초기화
        self.config = creditutil.InitializeConfig(env, member, month)
        self.cleanAllMonthResources()
        # 전전월 결제 상태 변경
        self.config.month = self.calcPrevMonth(month=2)
        # 전전월 미터링 전송
        self.sendPrevMonthMetering(month=2)
        # 결제 상태 변경
        self.sendPaymentsChange(month=2)
        # 연체료 배치 (연체료 - 전월 기준)
        self.sendBatchRequest(month=1)
        # 전월/당월 미터링 전송
        self.sendPrevMonthMetering(month=1)

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.beforeTest()

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self):
        yield
        self.sendPaymentsChange(month=0)

    def test_unpaid_TC1(self):
        self.sendPrevMonthMetering(month=0)
        prev_unpaid, cur_unpaid = self.compareUnpaid()
        # 결제 요청된 값, 실제 결제값(매출전표) 체크 및 전월 미납과 당일 미납 같은 지 체크
        statements, total_payments = self.config.commonTest()
        total_statements = statements['totalAmount'] - statements['totalCredit']
        supply_amount = (statements['charge'] + math.floor(statements['charge'] * 0.1))
        expect_unpaid_total = supply_amount + math.floor(supply_amount * 0.02)

        # 결제 금액 및 매출 전표 값 비교 assertion
        self.config.verifyAssert(statements=total_statements, payments=total_payments, expected_result=1500611,
                                 unpaid=True,
                                 prev_unpaid=prev_unpaid,
                                 current_unpaid=cur_unpaid,
                                 expect_unpaid_total=expect_unpaid_total)

    @staticmethod
    def calcPrevMonth(month):
        prev_month = datetime.now() - relativedelta(months=month)
        year, month = prev_month.year, prev_month.month
        month = "0" + prev_month.month.__str__() if prev_month.month < 10 else prev_month.month
        month_return = year.__str__() + "-" + month.__str__()
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
