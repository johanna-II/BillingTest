import logging
import math

import pytest

from libs.Calculation import CalculationManager
from libs.Contract import ContractManager as Contract
from libs.InitializeConfig import InitializeConfig
from libs.Metering import MeteringManager as Metering


def future_deprecated(func):
    def wrapper(*args):
        logging.warning(
            "주의: 이 테스트에서 사용하는 상품은 기간 약정이므로 기간 종료 시 테스트 실패할 수 있습니다."
        )
        return func(*args)

    return wrapper


@pytest.mark.core
@pytest.mark.billing
@pytest.mark.integration
@pytest.mark.mock_required
class TestContractOnly:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month, use_mock) -> None:
        self.config = InitializeConfig(env, member, month, use_mock=use_mock)

    @pytest.fixture(autouse=True)
    def setup(self, env, member, month, use_mock) -> None:
        self.config = InitializeConfig(env, member, month, use_mock=use_mock)

        # Reset test data for this UUID if using mock
        if use_mock:
            import requests

            try:
                response = requests.delete(
                    f"http://localhost:5000/test/reset/{self.config.uuid}"
                )
                if response.status_code == 200:
                    logging.info(f"Reset test data for UUID: {self.config.uuid}")
            except Exception as e:
                logging.warning(f"Failed to reset test data: {e}")

        self.config.before_test()  # to change paymentStatus as REGISTERED
        self.contractObj = Contract(self.config.month, self.config.billing_group_id[0])
        self.meteringObj = Metering(self.config.month)
        self.meteringObj.appkey = self.config.appkey[0]
        # Note: Metering data should be sent in each test case individually
        self.calcObj = CalculationManager(self.config.month, self.config.uuid)

    @pytest.fixture(autouse=True)
    def teardown(self, env, member, month):
        yield
        self.contractObj.delete_contract()
        self.config.clean_data()

    # 기간 약정 대비 미달 미터링 전송
    @future_deprecated
    def test_contractTC1(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        self.contractObj.apply_contract(contract_id="<contractID>")
        self.calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        total_statements = (
            statements["charge"]
            - statements.get("totalDiscount", 0)
            + statements.get("totalExtra", 0)
        )
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verify_assert(
            statements=total_amount_with_vat,
            payments=total_payments,
            expected_result=110000,
        )

    # 기간 약정 기준 초과 미터링 전송
    @future_deprecated
    def test_contractTC2(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="420",
        )
        self.contractObj.apply_contract(contract_id="<contractID>")
        self.calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        total_statements = (
            statements["charge"]
            - statements.get("totalDiscount", 0)
            + statements.get("totalExtra", 0)
        )
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verify_assert(
            statements=total_amount_with_vat,
            payments=total_payments,
            expected_result=128273,
        )

    # 볼륨 약정 대비 미달 미터링 전송
    def test_contractTC3(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        self.contractObj.apply_contract(contract_id="<contractID>")
        self.calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        total_statements = (
            statements["charge"]
            - statements.get("totalDiscount", 0)
            + statements.get("totalExtra", 0)
        )
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verify_assert(
            statements=total_amount_with_vat,
            payments=total_payments,
            expected_result=110000,
        )

    # 볼륨 약정 기준 초과 미터링 전송
    def test_contractTC4(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="500",
        )
        self.contractObj.apply_contract(contract_id="<contractID>")
        self.calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        total_statements = (
            statements["charge"]
            - statements.get("totalDiscount", 0)
            + statements.get("totalExtra", 0)
        )
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verify_assert(
            statements=total_amount_with_vat,
            payments=total_payments,
            expected_result=128273,
        )

    # 파트너 약정 대비 미달 미터링 전송
    def test_contractTC5(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="360",
        )
        self.contractObj.apply_contract(contract_id="<contractID>")
        self.calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        total_statements = (
            statements["charge"]
            - statements.get("totalDiscount", 0)
            + statements.get("totalExtra", 0)
        )
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verify_assert(
            statements=total_amount_with_vat,
            payments=total_payments,
            expected_result=110000,
        )

    # 파트너 약정 기준 초과 미터링 전송
    def test_contractTC6(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="500",
        )
        self.contractObj.apply_contract(contract_id="<contractID>")
        self.calcObj.recalculate_all()
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        total_statements = (
            statements["charge"]
            - statements.get("totalDiscount", 0)
            + statements.get("totalExtra", 0)
        )
        total_amount_with_vat = total_statements + math.floor(total_statements * 0.1)
        self.config.verify_assert(
            statements=total_amount_with_vat,
            payments=total_payments,
            expected_result=114523,
        )
