import math
import os

import pytest

from libs.InitializeConfig import InitializeConfig


@pytest.mark.core
@pytest.mark.credit
@pytest.mark.slow  # These tests make multiple API calls
@pytest.mark.mock_required
@pytest.mark.serial  # These tests must run serially due to shared state
class TestCreditAll:
    @pytest.fixture(autouse=True)
    def setup(self, env, member, month, use_mock) -> None:
        if member == "etc":
            pytest.skip(
                "Credit test should be skipped if member country is not KR or JP"
            )

        self.config = InitializeConfig(env, member, month, use_mock=use_mock)
        self.config.prepare()

        # Reset mock server data for this UUID if using mock server
        if os.environ.get("USE_MOCK_SERVER", "false").lower() == "true":
            import requests

            try:
                # Get mock server URL from environment or use default
                mock_url = os.environ.get("MOCK_SERVER_URL", "http://localhost:5000")
                # Use shorter timeout for faster tests
                response = requests.post(
                    f"{mock_url}/test/reset", json={"uuid": self.config.uuid}, timeout=1
                )
                if response.status_code == 200:
                    pass
            except Exception:
                pass

        # Get managers from config
        self.meteringObj = self.config.metering_manager
        self.credit = self.config.credit_manager
        self.calcObj = self.config.calculation_manager

        # Get app_key from config
        self.app_key = self.config.appkey[0] if self.config.appkey else "TEST-APP-KEY"
        # Store campaign_id for teardown
        self.used_campaign_ids = []

    @pytest.fixture(autouse=True)
    def teardown(self, env, member, month):
        yield
        # Cancel all used campaign credits
        if hasattr(self, "used_campaign_ids"):
            for campaign_id in self.used_campaign_ids:
                try:
                    self.credit.cancel_credit(campaign_id)
                except Exception:
                    pass  # Ignore errors during cleanup

    def test_creditTC1(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
            app_key=self.app_key,
        )
        self.calcObj.recalculate_all()
        campaign_id = (
            self.config.campaign_id[0] if self.config.campaign_id else "CAMPAIGN-001"
        )
        self.used_campaign_ids.append(campaign_id)
        self.credit.grant_credit(
            campaign_id,
            100000,
        )  # 100,000 / 무료, 지급형, 전체형 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        # statements["totalAmount"]은 이미 크레딧이 적용된 후의 금액
        # 따라서 statements_with_credit은 그냥 totalAmount와 같아야 함
        statements_with_credit = statements["totalAmount"]
        expect_result = (statements["charge"] - 100000) + math.floor(
            (statements["charge"] - 100000) * 0.1
        )
        credit_balance = self.credit.get_credit_balance()
        rest_credit = credit_balance["total"]
        total_credit_amt = credit_balance["total"]

        assert statements_with_credit == total_payments == expect_result
        assert rest_credit == total_credit_amt == 0

    def test_creditTC2(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.c2.c8m8",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
            app_key=self.app_key,
        )
        self.meteringObj.send_iaas_metering(
            counter_name="storage.volume.ssd",
            counter_type="DELTA",
            counter_unit="KB",
            counter_volume="524288000",
            app_key=self.app_key,
        )
        self.meteringObj.send_iaas_metering(
            counter_name="network.floating_ip",
            counter_type="DELTA",
            counter_unit="HOURS",
            counter_volume="720",
            app_key=self.app_key,
        )
        self.calcObj.recalculate_all()
        self.credit.grant_credit(
            self.config.campaign_id[0] if self.config.campaign_id else "CAMPAIGN-001",
            100000,
        )  # 100,000 / 무료, 쿠폰형, 이벤트 크레딧
        self.credit.grant_credit(
            self.config.campaign_id[0] if self.config.campaign_id else "CAMPAIGN-001",
            2000000,
        )  # 2,000,000 / 무료, 쿠폰형, 전체형 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        credit_balance = self.credit.get_credit_balance()
        rest_credit = credit_balance["total"]
        _total_credit_amt = credit_balance["total"]
        statements_with_credit = statements["totalAmount"]
        # 크레딧은 charge에서만 차감됨 (VAT 제외)
        expected_rest_credit = 2100000 - statements["charge"]
        assert statements_with_credit == total_payments == 0
        assert rest_credit == expected_rest_credit

    def test_creditTC3(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )
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
        self.calcObj.recalculate_all()
        self.credit.grant_credit(
            self.config.campaign_id[0] if self.config.campaign_id else "CAMPAIGN-001",
            2000000,
        )  # 2,000,000 / 무료, 지급형, 전체형 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        statements_with_credit = statements["totalAmount"]
        # 크레딧은 charge에서만 차감됨 (VAT 제외)
        expected_rest_credit = 2000000 - statements["charge"]
        credit_balance = self.credit.get_credit_balance()
        rest_credit = credit_balance["total"]
        _total_credit_amt = credit_balance["total"]
        assert statements_with_credit == total_payments == 0
        assert rest_credit == expected_rest_credit

    def test_creditTC4(self) -> None:
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
        self.calcObj.recalculate_all()
        self.credit.give_paid_credit(
            campaignId=(
                self.credit.paid_campaign_id[0]
                if self.credit.paid_campaign_id
                else "CAMPAIGN-001"
            ),
            creditAmount=100000,
        )  # 유료, 이벤트 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        statements_with_credit = statements["totalAmount"]
        credit_balance = self.credit.get_credit_balance()
        rest_credit = credit_balance["total"]
        total_credit_amt = credit_balance["total"]
        expect_result = (statements["charge"] - 100000) + math.floor(
            (statements["charge"] - 100000) * 0.1
        )
        assert statements_with_credit == total_payments == expect_result
        assert rest_credit == total_credit_amt == 0

    def test_creditTC5(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )
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
        self.calcObj.recalculate_all()
        self.credit.give_paid_credit(
            campaignId=(
                self.credit.paid_campaign_id[0]
                if self.credit.paid_campaign_id
                else "CAMPAIGN-001"
            ),
            creditAmount=2000000,
        )  # 유료, 전체형 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        statements_with_credit = statements["totalAmount"]
        # 크레딧은 charge에서만 차감됨 (VAT 제외)
        expected_rest_credit = 2000000 - statements["charge"]
        credit_balance = self.credit.get_credit_balance()
        rest_credit = credit_balance["total"]
        _total_credit_amt = credit_balance["total"]
        assert statements_with_credit == total_payments == 0
        assert rest_credit == expected_rest_credit

    def test_creditTC6(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )
        self.calcObj.recalculate_all()
        self.credit.give_paid_credit(
            campaignId=(
                self.credit.paid_campaign_id[0]
                if self.credit.paid_campaign_id
                else "CAMPAIGN-001"
            ),
            creditAmount=2000000,
        )  # 유료, 이벤트 크레딧
        self.credit.give_paid_credit(
            campaignId=(
                self.credit.paid_campaign_id[0]
                if self.credit.paid_campaign_id
                else "CAMPAIGN-001"
            ),
            creditAmount=100000,
        )  # 유료, 전체형 크레딧
        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        statements_with_credit = statements["totalAmount"]
        # mock server는 모든 크레딧을 동일하게 처리함
        # 2100000 크레딧 중 charge만큼 사용
        expected_rest_credit = 2100000 - statements["charge"]
        credit_balance = self.credit.get_credit_balance()
        rest_credit = credit_balance["total"]
        _total_credit_amt = credit_balance["total"]
        assert statements_with_credit == total_payments == 0
        assert rest_credit == expected_rest_credit

    def test_creditTC7(self) -> None:
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

        self.calcObj.recalculate_all()
        self.credit.grant_credit(
            self.config.campaign_id[0] if self.config.campaign_id else "CAMPAIGN-001",
            100000,
        )  # 무료, 쿠폰형, 전체형 크레딧
        self.credit.give_paid_credit(
            campaignId=(
                self.credit.paid_campaign_id[0]
                if self.credit.paid_campaign_id
                else "CAMPAIGN-001"
            ),
            creditAmount=2000000,
        )  # 유료, 전체형 크레딧

        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        statements_with_credit = statements["totalAmount"]
        credit_balance = self.credit.get_credit_balance()
        rest_credit = credit_balance["total"]
        _total_credit_amt = credit_balance["total"]
        # 크레딧은 charge에서만 차감됨 (VAT 제외)
        expected_rest_credit = 2100000 - statements["charge"]
        assert statements_with_credit == total_payments == 0
        assert rest_credit == expected_rest_credit

    def test_creditTC8(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )
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

        self.calcObj.recalculate_all()
        self.credit.grant_credit(
            self.config.campaign_id[0] if self.config.campaign_id else "CAMPAIGN-001",
            100000,
        )  # 무료, 지급형, 이벤트 크레딧
        self.credit.give_paid_credit(
            campaignId=(
                self.credit.paid_campaign_id[0]
                if self.credit.paid_campaign_id
                else "CAMPAIGN-001"
            ),
            creditAmount=100000,
        )  # 유료, 전체형 크레딧

        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        statements_with_credit = statements["totalAmount"]
        expect_result = (statements["charge"] - 200000) + math.floor(
            (statements["charge"] - 200000) * 0.1
        )
        credit_balance = self.credit.get_credit_balance()
        rest_credit = credit_balance["total"]
        _total_credit_amt = credit_balance["total"]
        assert statements_with_credit == total_payments == expect_result
        assert rest_credit == 0

    def test_creditTC9(self) -> None:
        self.meteringObj.send_iaas_metering(
            counter_name="compute.g2.t4.c8m64",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="720",
        )

        self.calcObj.recalculate_all()
        self.credit.grant_credit(
            self.config.campaign_id[0] if self.config.campaign_id else "CAMPAIGN-001",
            1000000,
        )  # 무료, 지급형, 이벤트 크레딧
        self.credit.give_paid_credit(
            campaignId=(
                self.credit.paid_campaign_id[0]
                if self.credit.paid_campaign_id
                else "CAMPAIGN-001"
            ),
            creditAmount=1000000,
        )  # 유료, 이벤트 크레딧

        # 결제 후 금액 비교
        statements, total_payments = self.config.common_test()
        credit_balance = self.credit.get_credit_balance()
        rest_credit = credit_balance["total"]
        _total_credit_amt = credit_balance["total"]
        # mock server는 모든 크레딧을 동일하게 처리함
        # 2000000 크레딧 중 charge만큼 사용
        expected_rest_credit = 2000000 - statements["charge"]
        assert statements["totalAmount"] == total_payments == 0
        assert rest_credit == expected_rest_credit
