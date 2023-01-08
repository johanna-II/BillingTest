import pytest
import libs.InitializeConfig as creditutil
import libs.Metering as metering
import libs.Contract as contract
import libs.Calculation as calc
import math
import logging


def futureDeprecated(func):
    def wrapper(*args):
        logging.warning('주의: 이 테스트에서 사용하는 상품은 기간 약정이므로 기간 종료 시 테스트 실패할 수 있습니다.')
        return func(*args)
    return wrapper


class TestContractOnly:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.cleanData()

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.beforeTest()  # to change paymentStatus as REGISTERED
        self.contractObj = contract.Contract(self.config.month, self.config.billing_group_id[0])
        self.meteringObj = metering.Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        self.meteringObj.sendIaaSMetering(counterName="storage.volume.ssd", counterType="DELTA", counterUnit="KB", counterVolume="524288000")
        self.meteringObj.sendIaaSMetering(counterName="network.floating_ip", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        self.calcObj = calc.Calculation(self.config.month, self.config.uuid)

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        self.contractObj.deleteContract()
        self.config.cleanMetering()

    # 기간 약정 대비 미달 미터링 전송
    @futureDeprecated
    def test_contractTC1(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="360")
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        total_statements = statements['charge'] - statements['totalDiscount'] + statements['totalExtra']
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verifyAssert(statements=total_amount_with_vat, payments=total_payments, expected_result=110000)

    # 기간 약정 기준 초과 미터링 전송
    @futureDeprecated
    def test_contractTC2(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="500")
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        total_statements = statements['charge'] - statements['totalDiscount'] + statements['totalExtra']
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verifyAssert(statements=total_amount_with_vat, payments=total_payments, expected_result=128273)

    # 볼륨 약정 대비 미달 미터링 전송
    def test_contractTC3(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="360")
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        total_statements = statements['charge'] - statements['totalDiscount'] + statements['totalExtra']
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verifyAssert(statements=total_amount_with_vat, payments=total_payments, expected_result=110000)

    # 볼륨 약정 기준 초과 미터링 전송
    def test_contractTC4(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="500")
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        total_statements = statements['charge'] - statements['totalDiscount'] + statements['totalExtra']
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verifyAssert(statements=total_amount_with_vat, payments=total_payments, expected_result=128273)

    # 파트너 약정 대비 미달 미터링 전송
    def test_contractTC5(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="360")
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        total_statements = statements['charge'] - statements['totalDiscount'] + statements['totalExtra']
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verifyAssert(statements=total_amount_with_vat, payments=total_payments, expected_result=110000)

    # 파트너 약정 기준 초과 미터링 전송
    def test_contractTC6(self):
        self.meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="500")
        self.contractObj.contractId = "<contractID>"
        self.contractObj.applyContract()
        self.calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        total_statements = statements['charge'] - statements['totalDiscount'] + statements['totalExtra']
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verifyAssert(statements=total_amount_with_vat, payments=total_payments, expected_result=114523)
