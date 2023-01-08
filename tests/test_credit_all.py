import pytest
import math
import libs.InitializeConfig as creditutil
import libs.Metering as metering
import libs.Credit as credit
import libs.Calculation as calc


class TestCreditAll:
    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        if member == "etc":
            pytest.skip("Credit test should be skipped if member country is not KR or JP")
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.cleanData()
        self.config.beforeTest()
        self.meteringObj = metering.Metering(month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.credit = credit.Credit()
        self.credit.uuid = self.config.uuid
        self.credit.campaign_id = self.config.campaign_id
        self.credit.give_campaign_id = self.config.give_campaign_id
        self.credit.paid_campaign_id = self.config.paid_campaign_id
        self.calcObj = calc.Calculation(self.config.month, self.config.uuid)

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        self.credit.cancelCredit()

    def test_creditTC1(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.g2.t4.c8m64", counterType="GAUGE", counterUnit="HOURS", counterVolume="720")
        self.calcObj.recalculationAll()
        self.credit.giveCredit("<creditCode>", 100000)  # 100,000 / 무료, 지급형, 전체형 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        statements_with_credit = statements['totalAmount'] - 100000
        expect_result = (statements['charge'] - 100000) + math.floor((statements['charge'] - 100000) * 0.1)
        rest_credit, total_credit_amt = self.credit.inquiryRestCredit()
        assert (statements_with_credit == total_payments == expect_result) & (rest_credit == total_credit_amt == 0)

    def test_creditTC2(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        self.meteringObj.sendIaaSMetering(counterName="storage.volume.ssd", counterType="DELTA", counterUnit="KB", counterVolume="524288000")
        self.meteringObj.sendIaaSMetering(counterName="network.floating_ip", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        self.calcObj.recalculationAll()
        self.credit.giveCredit("<creditCode>")  # 100,000 / 무료, 쿠폰형, 이벤트 크레딧
        self.credit.giveCredit("<creditCode>")  # 2,000,000 / 무료, 쿠폰형, 전체형 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        rest_credit, total_credit_amt = self.credit.inquiryRestCredit()
        statements_with_credit = statements['totalAmount'] - statements['totalCredit']
        expected_rest_credit = 2100000 - statements['totalAmount']
        assert (statements_with_credit == total_payments == 0) & (rest_credit == total_credit_amt == expected_rest_credit)

    def test_creditTC3(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.g2.t4.c8m64", counterType="GAUGE", counterUnit="HOURS", counterVolume="720")
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        self.meteringObj.sendIaaSMetering(counterName="storage.volume.ssd", counterType="DELTA", counterUnit="KB", counterVolume="524288000")
        self.calcObj.recalculationAll()
        self.credit.giveCredit("<creditCode>", 2000000)  # 2,000,000 / 무료, 지급형, 전체형 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        expected_rest_credit = 2000000 - statements['totalAmount']
        statements_with_credit = statements['totalAmount'] - statements['totalCredit']
        rest_credit, total_credit_amt = self.credit.inquiryRestCredit()
        assert (statements_with_credit == total_payments == 0) & (rest_credit == total_credit_amt == expected_rest_credit)

    def test_creditTC4(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        self.meteringObj.sendIaaSMetering(counterName="storage.volume.ssd", counterType="DELTA", counterUnit="KB", counterVolume="524288000")
        self.meteringObj.sendIaaSMetering(counterName="network.floating_ip", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        self.calcObj.recalculationAll()
        self.credit.givePaidCredit(campaignId="<creditCode>", creditAmount=100000)  # 유료, 이벤트 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        statements_with_credit = statements['totalAmount'] - 100000
        rest_credit, total_credit_amt = self.credit.inquiryRestCredit()
        expect_result = (statements['charge'] - 100000) + math.floor((statements['charge'] - 100000) * 0.1)
        assert (statements_with_credit == total_payments == expect_result) & (rest_credit == total_credit_amt == 0)

    def test_creditTC5(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.g2.t4.c8m64", counterType="GAUGE", counterUnit="HOURS", counterVolume="720")
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        self.meteringObj.sendIaaSMetering(counterName="storage.volume.ssd", counterType="DELTA", counterUnit="KB", counterVolume="524288000")
        self.meteringObj.sendIaaSMetering(counterName="network.floating_ip", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        self.calcObj.recalculationAll()
        self.credit.givePaidCredit(campaignId="<creditCode>", creditAmount=2000000)  # 유료, 전체형 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        expected_rest_credit = 2000000 - statements['totalAmount']
        statements_with_credit = statements['totalAmount'] - statements['totalCredit']
        rest_credit, total_credit_amt = self.credit.inquiryRestCredit()
        assert (statements_with_credit == total_payments == 0) & (rest_credit == total_credit_amt == expected_rest_credit)

    def test_creditTC6(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.g2.t4.c8m64", counterType="GAUGE", counterUnit="HOURS", counterVolume="720")
        self.calcObj.recalculationAll()
        self.credit.givePaidCredit(campaignId="<creditCode>", creditAmount=2000000)  # 유료, 이벤트 크레딧
        self.credit.givePaidCredit(campaignId="<creditCode>", creditAmount=100000)  # 유료, 전체형 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        statements_with_credit = statements['totalAmount'] - 100000
        expect_result = (statements['charge'] - 100000) + math.floor((statements['charge'] - 100000) * 0.1)
        rest_credit, total_credit_amt = self.credit.inquiryRestCredit()
        assert (statements_with_credit == total_payments == expect_result) & (rest_credit == total_credit_amt == 2000000)

    def test_creditTC7(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        self.meteringObj.sendIaaSMetering(counterName="storage.volume.ssd", counterType="DELTA", counterUnit="KB", counterVolume="524288000")
        self.meteringObj.sendIaaSMetering(counterName="network.floating_ip", counterType="DELTA", counterUnit="HOURS", counterVolume="720")

        self.calcObj.recalculationAll()
        self.credit.giveCredit("<creditCode>")  # 무료, 쿠폰형, 전체형 크레딧
        self.credit.givePaidCredit(campaignId="<creditCode>", creditAmount=2000000)  # 유료, 전체형 크레딧

        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        statements_with_credit = statements['totalAmount'] - statements['totalCredit']
        rest_credit, total_credit_amt = self.credit.inquiryRestCredit()
        expected_rest_credit = 2000000 - statements['totalAmount']
        assert (statements_with_credit == total_payments == 0) & (rest_credit == total_credit_amt == expected_rest_credit)

    def test_creditTC8(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.g2.t4.c8m64", counterType="GAUGE", counterUnit="HOURS", counterVolume="720")
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        self.meteringObj.sendIaaSMetering(counterName="storage.volume.ssd", counterType="DELTA", counterUnit="KB", counterVolume="524288000")
        self.meteringObj.sendIaaSMetering(counterName="network.floating_ip", counterType="DELTA", counterUnit="HOURS", counterVolume="720")

        self.calcObj.recalculationAll()
        self.credit.giveCredit("<creditCode>", 100000)  # 무료, 지급형, 이벤트 크레딧
        self.credit.givePaidCredit(campaignId="<creditCode>", creditAmount=100000)  # 유료, 전체형 크레딧

        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        statements_with_credit = statements['totalAmount'] - statements['totalCredit']
        expect_result = (statements['charge'] - 200000) + math.floor((statements['charge'] - 200000) * 0.1)
        rest_credit, total_credit_amt = self.credit.inquiryRestCredit()
        assert (statements_with_credit == total_payments == expect_result) & (rest_credit == total_credit_amt == 0)

    def test_creditTC9(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.g2.t4.c8m64", counterType="GAUGE", counterUnit="HOURS", counterVolume="720")

        self.calcObj.recalculationAll()
        self.credit.giveCredit("<creditCode>", 1000000)  # 무료, 지급형, 이벤트 크레딧
        self.credit.givePaidCredit(campaignId="<creditCode>", creditAmount=1000000)  # 유료, 이벤트 크레딧

        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        rest_credit, total_credit_amt = self.credit.inquiryRestCredit()
        expect_result = statements['charge'] + math.floor(statements['charge'] * 0.1)
        assert (statements['totalAmount'] == total_payments == expect_result) & (rest_credit == total_credit_amt == 2000000)
