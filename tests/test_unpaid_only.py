import pytest
from libs.InitializeConfig import InitializeConfig
from libs.Metering import MeteringManager as Metering
from libs.Payments import PaymentManager as Payments
from libs.Batch import BatchManager as Batches
import libs.Calculation as calc
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TestUnpaidOnly:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        # 초기화
        self.config = InitializeConfig(env, member, month)
        self.clean_all_month_resources()
        # 전전월 결제 상태 변경
        self.config.month = self.calc_prev_month(month=2)
        # 전전월 미터링 전송
        self.send_prev_month_metering(month=2)
        # 결제 상태 변경
        self.send_payments_change(month=2)
        # 연체료 배치 (연체료 - 전월 기준)
        self.send_batch_request(month=1)
        # 전월/당월 미터링 전송
        self.send_prev_month_metering(month=1)

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = InitializeConfig(env, member, month)
        self.config.before_test()

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self):
        yield
        self.send_payments_change(month=0)

    def test_unpaid_TC1(self):
        self.send_prev_month_metering(month=0)
        prev_unpaid, cur_unpaid = self.compare_unpaid()
        # 결제 요청된 값, 실제 결제값(매출전표) 체크 및 전월 미납과 당일 미납 같은 지 체크
        statements, total_payments = self.config.common_test()
        total_statements = statements["totalAmount"] - statements["totalCredit"]
        supply_amount = statements["charge"] + math.floor(statements["charge"] * 0.1)
        expect_unpaid_total = supply_amount + math.floor(supply_amount * 0.02)

        # 결제 금액 및 매출 전표 값 비교 assertion
        self.config.verify_assert(
            statements=total_statements,
            payments=total_payments,
            expected_result=1500611,
            unpaid=True,
            prev_unpaid=prev_unpaid,
            current_unpaid=cur_unpaid,
            expect_unpaid_total=expect_unpaid_total,
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
        month_return = year.__str__() + "-" + month.__str__()
        return month_return

    def send_prev_month_metering(self, month):
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

    def send_payments_change(self, month):
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
            print("++ 결제 상태 : READY, skipped change status")

    def send_batch_request(self, month):
        month = self.calc_prev_month(month=month)
        batchObj = Batches(month)
        batchObj.month = self.config.month = month
        batchObj.batch_job_code = "CALC_LATE_FEE"
        batchObj.send_batch_request()

    def clean_all_month_resources(self):
        # 모든 월 초기화 처리
        for idx in range(3):
            month = self.calc_prev_month(month=idx)
            self.config.month = month

    def compare_unpaid(self):
        prev_month = self.calc_prev_month(month=1)
        paymentsObj = Payments(prev_month)
        paymentsObj.uuid = self.config.uuid
        prev_unpaid = paymentsObj.unpaid()
        cur_month = self.calc_prev_month(month=0)
        paymentsObj = Payments(cur_month)
        paymentsObj.uuid = self.config.uuid
        cur_unpaid = paymentsObj.unpaid()
        print(
            f"{prev_month}월 미납 금액: {prev_unpaid}, {cur_month}월 미납 금액: {cur_unpaid}"
        )
        return prev_unpaid, cur_unpaid
