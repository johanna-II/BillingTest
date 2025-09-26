"""Comprehensive contract tests for all billing libraries to improve code coverage."""

import os

import pytest
from pact import Consumer, Like, Provider, Term

from libs.Adjustment import AdjustmentManager
from libs.Batch import BatchManager
from libs.Calculation import CalculationManager
from libs.constants import (
    AdjustmentTarget,
    AdjustmentType,
    BatchJobCode,
    CounterType,
    CreditType,
    PaymentStatus,
)
from libs.Contract import ContractManager
from libs.Credit import CreditManager
from libs.http_client import BillingAPIClient
from libs.InitializeConfig import InitializeConfig
from libs.Metering import MeteringManager
from libs.Payments import PaymentManager

# Pact configuration
PACT_DIR = os.path.join(os.path.dirname(__file__), "pacts")
os.makedirs(PACT_DIR, exist_ok=True)


@pytest.fixture(scope="session")
def comprehensive_pact():
    """Set up comprehensive Pact consumer."""
    consumer = Consumer("BillingTestComprehensive")
    provider = Provider("BillingAPIComprehensive")

    pact = consumer.has_pact_with(provider, pact_dir=PACT_DIR)

    pact.start_service()
    yield pact
    pact.stop_service()


@pytest.fixture
def api_client(comprehensive_pact):
    """Create API client for pact testing."""
    return BillingAPIClient(
        base_url=f"http://localhost:{comprehensive_pact.port}/api/v1"
    )


@pytest.mark.contract
@pytest.mark.integration
class TestAdjustmentManagerContracts:
    """Contract tests for AdjustmentManager to improve coverage from 19.01%."""

    def test_apply_adjustment(self, comprehensive_pact, api_client):
        """Test applying various types of adjustments."""
        # Expected response
        expected = {
            "adjustmentId": Term(r"[A-Z0-9-]+", "ADJ-001"),
            "status": Like("SUCCESS"),
            "amount": Like(1000.0),
            "type": Like("FIXED_DISCOUNT"),
            "target": Like("BILLING_GROUP"),
        }

        # Define interaction
        (
            comprehensive_pact.given("Billing group exists")
            .upon_receiving("Request to apply fixed discount adjustment")
            .with_request(
                "POST",
                "/api/v1/adjustments",
                headers={"Content-Type": "application/json"},
                body={
                    "adjustment_amount": 1000.0,
                    "adjustment_type": "FIXED_DISCOUNT",
                    "adjustment_target": "BILLING_GROUP",
                    "target_id": "BG-001",
                    "description": "Test adjustment",
                    "month": "2025-01",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = AdjustmentManager(month="2025-01", client=api_client)

            # Test fixed discount
            result = manager.apply_adjustment(
                adjustment_amount=1000.0,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
                target_id="BG-001",
                description="Test adjustment",
            )
            assert "adjustmentId" in result

    def test_apply_percentage_adjustment(self, comprehensive_pact, api_client):
        """Test percentage-based adjustments."""
        expected = {
            "adjustmentId": Term(r"[A-Z0-9-]+", "ADJ-002"),
            "status": Like("SUCCESS"),
            "rate": Like(10.0),
            "type": Like("RATE_DISCOUNT"),
        }

        (
            comprehensive_pact.given("Project exists")
            .upon_receiving("Request to apply percentage discount")
            .with_request(
                "POST",
                "/api/v1/adjustments",
                headers={"Content-Type": "application/json"},
                body={
                    "adjustment_amount": 10.0,
                    "adjustment_type": "RATE_DISCOUNT",
                    "adjustment_target": "PROJECT",
                    "target_id": "PROJ-001",
                    "month": "2025-01",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = AdjustmentManager(month="2025-01", client=api_client)

            # Test rate discount
            result = manager.apply_adjustment(
                adjustment_amount=10.0,
                adjustment_type=AdjustmentType.RATE_DISCOUNT,
                adjustment_target=AdjustmentTarget.PROJECT,
                target_id="PROJ-001",
            )
            assert result.get("status") == "SUCCESS"

    def test_get_adjustments(self, comprehensive_pact, api_client):
        """Test retrieving adjustments with pagination."""
        expected = {
            "adjustments": Like(
                [
                    {
                        "adjustmentId": Like("ADJ-001"),
                        "amount": Like(1000.0),
                        "type": Like("FIXED_DISCOUNT"),
                        "target": Like("BILLING_GROUP"),
                        "targetId": Like("BG-001"),
                        "createdAt": Term(
                            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
                            "2025-01-01T00:00:00",
                        ),
                    }
                ]
            ),
            "total": Like(5),
            "page": Like(1),
            "hasMore": Like(True),
        }

        (
            comprehensive_pact.given("Multiple adjustments exist")
            .upon_receiving("Request to get adjustments")
            .with_request(
                "GET",
                "/api/v1/adjustments",
                query={
                    "adjustment_target": "BILLING_GROUP",
                    "target_id": "BG-001",
                    "month": "2025-01",
                    "page": "1",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = AdjustmentManager(month="2025-01", client=api_client)

            # Test get adjustments
            adjustments = manager.get_adjustments(
                adjustment_target=AdjustmentTarget.BILLING_GROUP, target_id="BG-001"
            )
            assert isinstance(adjustments, list)

    def test_delete_adjustment(self, comprehensive_pact, api_client):
        """Test deleting adjustments."""
        expected = {
            "status": Like("DELETED"),
            "deletedCount": Like(1),
            "adjustmentIds": Like(["ADJ-001"]),
        }

        (
            comprehensive_pact.given("Adjustment exists")
            .upon_receiving("Request to delete adjustment")
            .with_request(
                "DELETE",
                "/api/v1/adjustments/ADJ-001",
                headers={"Content-Type": "application/json"},
                body={"adjustment_target": "BILLING_GROUP", "month": "2025-01"},
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = AdjustmentManager(month="2025-01", client=api_client)

            # Test delete
            result = manager.delete_adjustment(
                adjustment_ids="ADJ-001",
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
            )
            assert result.get("status") == "DELETED"


@pytest.mark.contract
@pytest.mark.integration
class TestContractManagerContracts:
    """Contract tests for ContractManager to improve coverage from 17.02%."""

    def test_apply_contract(self, comprehensive_pact, api_client):
        """Test applying contracts."""
        expected = {
            "status": Like("SUCCESS"),
            "contractId": Like("CONTRACT-001"),
            "billingGroupId": Like("BG-001"),
            "appliedAt": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:00:00"
            ),
        }

        (
            comprehensive_pact.given("Contract template exists")
            .upon_receiving("Request to apply contract")
            .with_request(
                "POST",
                "/api/v1/contracts/apply",
                headers={"Content-Type": "application/json"},
                body={
                    "contract_id": "CONTRACT-001",
                    "name": "Standard Contract",
                    "billing_group_id": "BG-001",
                    "month": "2025-01",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = ContractManager(
                month="2025-01", billing_group_id="BG-001", client=api_client
            )

            # Test apply contract
            result = manager.apply_contract(
                contract_id="CONTRACT-001", name="Standard Contract"
            )
            assert result.get("status") == "SUCCESS"

    def test_check_applied_contracts(self, comprehensive_pact, api_client):
        """Test checking applied contracts."""
        expected = {
            "contracts": Like(
                [
                    {
                        "contractId": Like("CONTRACT-001"),
                        "name": Like("Standard Contract"),
                        "status": Like("ACTIVE"),
                        "appliedDate": Term(r"\d{4}-\d{2}-\d{2}", "2025-01-01"),
                    }
                ]
            ),
            "total": Like(1),
            "billingGroupId": Like("BG-001"),
        }

        (
            comprehensive_pact.given("Contracts are applied")
            .upon_receiving("Request to check applied contracts")
            .with_request(
                "GET",
                "/api/v1/contracts/applied",
                query={"billing_group_id": "BG-001", "month": "2025-01"},
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = ContractManager(
                month="2025-01", billing_group_id="BG-001", client=api_client
            )

            # Test check applied contracts
            contracts = manager.check_applied_contracts()
            assert isinstance(contracts, list)

    def test_get_contract_details(self, comprehensive_pact, api_client):
        """Test getting contract details."""
        expected = {
            "contractType": Like("Basic"),
            "details": {
                "basePrice": Like(1000.0),
                "includedServices": Like(["compute", "storage"]),
                "terms": Like("monthly"),
                "discountRate": Like(5.0),
            },
            "metadata": {
                "version": Like("1.0"),
                "lastUpdated": Term(r"\d{4}-\d{2}-\d{2}", "2025-01-01"),
            },
        }

        (
            comprehensive_pact.given("Contract exists")
            .upon_receiving("Request for contract details")
            .with_request("GET", "/api/v1/contracts/CONTRACT-001/details")
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = ContractManager(
                month="2025-01", billing_group_id="BG-001", client=api_client
            )

            # Test get contract details
            details = manager.get_contract_details("CONTRACT-001")
            assert "contractType" in details
            assert "details" in details


@pytest.mark.contract
@pytest.mark.integration
class TestBatchManagerContracts:
    """Contract tests for BatchManager to improve coverage from 27.42%."""

    def test_request_batch_job(self, comprehensive_pact, api_client):
        """Test requesting batch jobs."""
        expected = {
            "batchId": Term(r"[A-Z0-9-]+", "BATCH-001"),
            "jobCode": Like("BATCH_CREDIT_EXPIRY"),
            "status": Like("PENDING"),
            "createdAt": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:00:00"
            ),
        }

        (
            comprehensive_pact.given("Batch processing is available")
            .upon_receiving("Request to start credit expiry batch")
            .with_request(
                "POST",
                "/api/v1/batch/jobs",
                headers={"Content-Type": "application/json"},
                body={
                    "job_code": "BATCH_CREDIT_EXPIRY",
                    "month": "2025-01",
                    "execution_day": 1,
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = BatchManager(month="2025-01", client=api_client)

            # Test request batch job
            result = manager.request_batch_job(
                job_code=BatchJobCode.BATCH_CREDIT_EXPIRY, execution_day=1
            )
            assert "batchId" in result

    def test_get_batch_status(self, comprehensive_pact, api_client):
        """Test getting batch job status."""
        expected = {
            "status": Like("COMPLETED"),
            "jobCode": Like("BATCH_CREDIT_EXPIRY"),
            "progress": Like(100),
            "startTime": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:00:00"
            ),
            "endTime": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T01:00:00"
            ),
            "recordsProcessed": Like(1000),
        }

        (
            comprehensive_pact.given("Batch job exists")
            .upon_receiving("Request for batch job status")
            .with_request(
                "GET",
                "/api/v1/batch/jobs/status",
                query={"job_code": "BATCH_CREDIT_EXPIRY", "month": "2025-01"},
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = BatchManager(month="2025-01", client=api_client)

            # Test get batch status
            status = manager.get_batch_status(BatchJobCode.BATCH_CREDIT_EXPIRY)
            assert "status" in status
            assert status["status"] in ["PENDING", "RUNNING", "COMPLETED", "FAILED"]

    def test_request_common_batch_jobs(self, comprehensive_pact, api_client):
        """Test requesting common batch jobs."""
        # Expected responses for multiple batch jobs
        batch_responses = {
            "credit_expiry": {
                "batchId": Like("BATCH-001"),
                "jobCode": Like("BATCH_CREDIT_EXPIRY"),
                "status": Like("PENDING"),
            },
            "calculation": {
                "batchId": Like("BATCH-002"),
                "jobCode": Like("BATCH_PAYMENT_CALCULATION"),
                "status": Like("PENDING"),
            },
            "statement": {
                "batchId": Like("BATCH-003"),
                "jobCode": Like("BATCH_GENERATE_STATEMENT"),
                "status": Like("PENDING"),
            },
        }

        # Set up multiple interactions
        (
            comprehensive_pact.given("Batch processing is available")
            .upon_receiving("Request for credit expiry batch")
            .with_request(
                "POST",
                "/api/v1/batch/jobs",
                headers={"Content-Type": "application/json"},
                body={
                    "job_code": "BATCH_CREDIT_EXPIRY",
                    "month": "2025-01",
                    "execution_day": 1,
                },
            )
            .will_respond_with(200, body=batch_responses["credit_expiry"])
        )

        with comprehensive_pact:
            manager = BatchManager(month="2025-01", client=api_client)

            # Test request common batch jobs
            results = manager.request_common_batch_jobs()
            assert len(results) > 0


@pytest.mark.contract
@pytest.mark.integration
class TestCalculationManagerContracts:
    """Contract tests for CalculationManager to improve coverage from 26.53%."""

    def test_recalculate_all(self, comprehensive_pact, api_client):
        """Test recalculation with various options."""
        expected = {
            "status": Like("STARTED"),
            "calculationId": Term(r"[A-Z0-9-]+", "CALC-001"),
            "includeUsage": Like(True),
            "startTime": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:00:00"
            ),
        }

        (
            comprehensive_pact.given("Billing data exists")
            .upon_receiving("Request to recalculate all")
            .with_request(
                "POST",
                "/api/v1/calculations/recalculate",
                headers={"Content-Type": "application/json"},
                body={
                    "month": "2025-01",
                    "uuid": "UUID-001",
                    "include_usage": True,
                    "timeout": 300,
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = CalculationManager(
                month="2025-01", uuid="UUID-001", client=api_client
            )

            # Test recalculate all
            result = manager.recalculate_all(include_usage=True, timeout=300)
            assert result.get("status") in ["STARTED", "COMPLETED"]

    def test_calculate_specific_items(self, comprehensive_pact, api_client):
        """Test calculating specific items."""
        expected = {
            "status": Like("COMPLETED"),
            "itemsCalculated": Like(["ITEM-001", "ITEM-002"]),
            "totalAmount": Like(5000.0),
            "currency": Like("USD"),
        }

        (
            comprehensive_pact.given("Items exist for calculation")
            .upon_receiving("Request to calculate specific items")
            .with_request(
                "POST",
                "/api/v1/calculations/items",
                headers={"Content-Type": "application/json"},
                body={
                    "month": "2025-01",
                    "uuid": "UUID-001",
                    "items": ["ITEM-001", "ITEM-002"],
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = CalculationManager(
                month="2025-01", uuid="UUID-001", client=api_client
            )

            # Test calculate specific
            result = manager.calculate_specific_items(["ITEM-001", "ITEM-002"])
            assert "itemsCalculated" in result

    def test_get_calculation_status(self, comprehensive_pact, api_client):
        """Test getting calculation status."""
        expected = {
            "status": Like("COMPLETED"),
            "progress": Like(100),
            "startTime": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:00:00"
            ),
            "endTime": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:10:00"
            ),
            "itemsProcessed": Like(50),
            "errors": Like([]),
        }

        (
            comprehensive_pact.given("Calculation is running")
            .upon_receiving("Request for calculation status")
            .with_request(
                "GET",
                "/api/v1/calculations/status",
                query={"calculation_id": "CALC-001", "month": "2025-01"},
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = CalculationManager(
                month="2025-01", uuid="UUID-001", client=api_client
            )

            # Test get status
            status = manager.get_calculation_status("CALC-001")
            assert "status" in status


@pytest.mark.contract
@pytest.mark.integration
class TestMeteringManagerContracts:
    """Contract tests for MeteringManager to improve coverage from 25.00%."""

    def test_send_metering(self, comprehensive_pact, api_client):
        """Test sending metering data."""
        expected = {
            "status": Like("SUCCESS"),
            "meteringId": Term(r"[A-Z0-9-]+", "METER-001"),
            "accepted": Like(True),
            "timestamp": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:00:00"
            ),
        }

        (
            comprehensive_pact.given("Metering endpoint is available")
            .upon_receiving("Request to send metering data")
            .with_request(
                "POST",
                "/api/v1/metering",
                headers={"Content-Type": "application/json"},
                body={
                    "app_key": "APP-001",
                    "counter_name": "compute.cpu.hours",
                    "counter_type": "DELTA",
                    "counter_unit": "HOURS",
                    "counter_volume": "100",
                    "month": "2025-01",
                    "timestamp": Like("2025-01-01T00:00:00"),
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = MeteringManager(month="2025-01", client=api_client)

            # Test send metering
            result = manager.send_metering(
                app_key="APP-001",
                counter_name="compute.cpu.hours",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume="100",
            )
            assert result.get("status") == "SUCCESS"

    def test_send_batch_metering(self, comprehensive_pact, api_client):
        """Test sending batch metering data."""
        expected = {
            "status": Like("SUCCESS"),
            "accepted": Like(10),
            "rejected": Like(0),
            "batchId": Term(r"[A-Z0-9-]+", "BATCH-METER-001"),
        }

        (
            comprehensive_pact.given("Batch metering is enabled")
            .upon_receiving("Request to send batch metering")
            .with_request(
                "POST",
                "/api/v1/metering/batch",
                headers={"Content-Type": "application/json"},
                body={
                    "month": "2025-01",
                    "meters": Like(
                        [
                            {
                                "app_key": "APP-001",
                                "counter_name": "compute.cpu.hours",
                                "counter_type": "DELTA",
                                "counter_unit": "HOURS",
                                "counter_volume": "100",
                            }
                        ]
                    ),
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = MeteringManager(month="2025-01", client=api_client)

            # Test batch metering
            meters = [
                {
                    "app_key": "APP-001",
                    "counter_name": "compute.cpu.hours",
                    "counter_type": CounterType.DELTA,
                    "counter_unit": "HOURS",
                    "counter_volume": "100",
                }
                for _ in range(10)
            ]
            result = manager.send_batch_metering(meters)
            assert result.get("accepted") == 10

    def test_get_metering_summary(self, comprehensive_pact, api_client):
        """Test getting metering summary."""
        expected = {
            "summary": {
                "total_meters": Like(100),
                "by_type": {"DELTA": Like(60), "GAUGE": Like(40)},
                "by_app": Like(
                    [
                        {
                            "app_key": Like("APP-001"),
                            "count": Like(50),
                            "total_volume": Like(5000.0),
                        }
                    ]
                ),
            },
            "period": {
                "start": Term(r"\d{4}-\d{2}-\d{2}", "2025-01-01"),
                "end": Term(r"\d{4}-\d{2}-\d{2}", "2025-01-31"),
            },
        }

        (
            comprehensive_pact.given("Metering data exists")
            .upon_receiving("Request for metering summary")
            .with_request(
                "GET",
                "/api/v1/metering/summary",
                query={"month": "2025-01", "app_key": "APP-001"},
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = MeteringManager(month="2025-01", client=api_client)

            # Test get summary
            summary = manager.get_metering_summary(app_key="APP-001")
            assert "summary" in summary


@pytest.mark.contract
@pytest.mark.integration
class TestPaymentManagerContracts:
    """Contract tests for PaymentManager to improve coverage from 24.70%."""

    def test_get_payment_status(self, comprehensive_pact, api_client):
        """Test getting payment status."""
        expected = {
            "paymentGroupId": Term(r"[A-Z0-9-]+", "PG-001"),
            "status": Like("PENDING"),
            "amount": Like(5000.0),
            "currency": Like("USD"),
            "dueDate": Term(r"\d{4}-\d{2}-\d{2}", "2025-02-01"),
        }

        (
            comprehensive_pact.given("Payment exists")
            .upon_receiving("Request for payment status")
            .with_request(
                "GET",
                "/api/v1/payments/status",
                query={"month": "2025-01", "uuid": "UUID-001"},
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = PaymentManager(
                month="2025-01", uuid="UUID-001", client=api_client
            )

            # Test get payment status
            pg_id, status = manager.get_payment_status()
            assert pg_id is not None
            assert status in [s.value for s in PaymentStatus]

    def test_check_unpaid_amount(self, comprehensive_pact, api_client):
        """Test checking unpaid amount."""
        expected = {
            "unpaidAmount": Like(3000.0),
            "totalAmount": Like(5000.0),
            "paidAmount": Like(2000.0),
            "currency": Like("USD"),
            "breakdown": Like(
                [
                    {"type": Like("usage"), "amount": Like(4000.0)},
                    {"type": Like("adjustment"), "amount": Like(-1000.0)},
                ]
            ),
        }

        (
            comprehensive_pact.given("Payment with partial payment exists")
            .upon_receiving("Request for unpaid amount")
            .with_request("GET", "/api/v1/payments/PG-001/unpaid")
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = PaymentManager(
                month="2025-01", uuid="UUID-001", client=api_client
            )

            # Test check unpaid
            amount = manager.check_unpaid_amount("PG-001")
            assert amount >= 0

    def test_make_payment(self, comprehensive_pact, api_client):
        """Test making payment."""
        expected = {
            "status": Like("PROCESSING"),
            "transactionId": Term(r"[A-Z0-9-]+", "TXN-001"),
            "paymentGroupId": Like("PG-001"),
            "amount": Like(3000.0),
            "processedAt": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-15T10:00:00"
            ),
        }

        (
            comprehensive_pact.given("Payment can be processed")
            .upon_receiving("Request to make payment")
            .with_request(
                "POST",
                "/api/v1/payments/PG-001/pay",
                headers={"Content-Type": "application/json"},
                body={"payment_method": "CREDIT_CARD", "amount": 3000.0},
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = PaymentManager(
                month="2025-01", uuid="UUID-001", client=api_client
            )

            # Test make payment
            result = manager.make_payment("PG-001", payment_method="CREDIT_CARD")
            assert "transactionId" in result

    def test_get_payment_history(self, comprehensive_pact, api_client):
        """Test getting payment history."""
        expected = {
            "history": Like(
                [
                    {
                        "paymentId": Like("PAY-001"),
                        "amount": Like(1000.0),
                        "status": Like("COMPLETED"),
                        "paidAt": Term(
                            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
                            "2025-01-10T10:00:00",
                        ),
                        "method": Like("CREDIT_CARD"),
                    }
                ]
            ),
            "total": Like(5),
            "totalPaid": Like(5000.0),
        }

        (
            comprehensive_pact.given("Payment history exists")
            .upon_receiving("Request for payment history")
            .with_request(
                "GET",
                "/api/v1/payments/history",
                query={
                    "uuid": "UUID-001",
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = PaymentManager(
                month="2025-01", uuid="UUID-001", client=api_client
            )

            # Test get history
            history = manager.get_payment_history(
                start_date="2025-01-01", end_date="2025-01-31"
            )
            assert isinstance(history, list)


@pytest.mark.contract
@pytest.mark.integration
class TestCreditManagerContracts:
    """Contract tests for CreditManager to improve coverage from 31.95%."""

    def test_grant_credit_to_users(self, comprehensive_pact, api_client):
        """Test granting credits to users."""
        expected = {
            "success_count": Like(3),
            "failed_count": Like(0),
            "credits": Like(
                [
                    {
                        "creditId": Term(r"[A-Z0-9-]+", "CREDIT-001"),
                        "uuid": Like("UUID-001"),
                        "amount": Like(1000.0),
                        "type": Like("CAMPAIGN"),
                        "status": Like("ACTIVE"),
                    }
                ]
            ),
        }

        (
            comprehensive_pact.given("Users exist")
            .upon_receiving("Request to grant credits")
            .with_request(
                "POST",
                "/api/v1/credits/grant",
                headers={"Content-Type": "application/json"},
                body={
                    "credit_amount": 1000.0,
                    "credit_type": "CAMPAIGN",
                    "user_list": ["UUID-001", "UUID-002", "UUID-003"],
                    "description": "Campaign credit",
                    "expires_in_days": 30,
                },
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = CreditManager(uuid="UUID-001", client=api_client)

            # Test grant credit
            result = manager.grant_credit_to_users(
                credit_amount=1000.0,
                credit_type=CreditType.CAMPAIGN,
                user_list=["UUID-001", "UUID-002", "UUID-003"],
                description="Campaign credit",
                expires_in_days=30,
            )
            assert result["success_count"] == 3

    def test_get_credit_balance(self, comprehensive_pact, api_client):
        """Test getting credit balance with details."""
        expected = {
            "totalBalance": Like(5000.0),
            "byType": {
                "CAMPAIGN": Like(2000.0),
                "REFUND": Like(1500.0),
                "BONUS": Like(1500.0),
            },
            "credits": Like(
                [
                    {
                        "creditId": Like("CREDIT-001"),
                        "type": Like("CAMPAIGN"),
                        "amount": Like(2000.0),
                        "remaining": Like(1500.0),
                        "expiresAt": Term(r"\d{4}-\d{2}-\d{2}", "2025-02-01"),
                    }
                ]
            ),
        }

        (
            comprehensive_pact.given("User has multiple credits")
            .upon_receiving("Request for credit balance")
            .with_request("GET", "/api/v1/credits/balance", query={"uuid": "UUID-001"})
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = CreditManager(uuid="UUID-001", client=api_client)

            # Test get balance
            balance = manager.get_total_credit_balance()
            assert balance >= 0

            # Test get detailed balance
            details = manager.get_credit_balance_details()
            assert "byType" in details

    def test_use_coupon(self, comprehensive_pact, api_client):
        """Test using coupon code."""
        expected = {
            "success": Like(True),
            "creditId": Term(r"[A-Z0-9-]+", "CREDIT-002"),
            "amount": Like(500.0),
            "couponCode": Like("WELCOME2025"),
            "message": Like("Coupon applied successfully"),
        }

        (
            comprehensive_pact.given("Valid coupon exists")
            .upon_receiving("Request to use coupon")
            .with_request(
                "POST",
                "/api/v1/credits/coupon",
                headers={"Content-Type": "application/json"},
                body={"coupon_code": "WELCOME2025", "uuid": "UUID-001"},
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = CreditManager(uuid="UUID-001", client=api_client)

            # Test use coupon
            result = manager.use_coupon("WELCOME2025")
            assert result.get("success") is True

    def test_get_credit_history(self, comprehensive_pact, api_client):
        """Test getting credit history with pagination."""
        expected = {
            "total_amount": Like(10000.0),
            "history": Like(
                [
                    {
                        "creditId": Like("CREDIT-001"),
                        "type": Like("CAMPAIGN"),
                        "amount": Like(1000.0),
                        "remaining": Like(500.0),
                        "createdAt": Term(
                            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
                            "2025-01-01T00:00:00",
                        ),
                        "usedAmount": Like(500.0),
                        "status": Like("ACTIVE"),
                    }
                ]
            ),
            "pagination": {
                "total": Like(50),
                "page": Like(1),
                "pageSize": Like(10),
                "hasMore": Like(True),
            },
        }

        (
            comprehensive_pact.given("Credit history exists")
            .upon_receiving("Request for credit history")
            .with_request(
                "GET",
                "/api/v1/credits/history",
                query={"uuid": "UUID-001", "page": "1", "items_per_page": "10"},
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = CreditManager(uuid="UUID-001", client=api_client)

            # Test get history
            total, history = manager.get_credit_history(items_per_page=10)
            assert total >= 0
            assert isinstance(history, list)

    def test_cancel_credit(self, comprehensive_pact, api_client):
        """Test cancelling credit."""
        expected = {
            "status": Like("CANCELLED"),
            "creditId": Like("CREDIT-001"),
            "cancelledAmount": Like(500.0),
            "reason": Like("Customer request"),
        }

        (
            comprehensive_pact.given("Active credit exists")
            .upon_receiving("Request to cancel credit")
            .with_request(
                "POST",
                "/api/v1/credits/CREDIT-001/cancel",
                headers={"Content-Type": "application/json"},
                body={"reason": "Customer request", "uuid": "UUID-001"},
            )
            .will_respond_with(200, body=expected)
        )

        with comprehensive_pact:
            manager = CreditManager(uuid="UUID-001", client=api_client)

            # Test cancel credit
            result = manager.cancel_credit("CREDIT-001", reason="Customer request")
            assert result.get("status") == "CANCELLED"


@pytest.mark.contract
@pytest.mark.integration
class TestInitializeConfigContracts:
    """Contract tests for InitializeConfig to improve coverage from 35.93%."""

    def test_initialize_with_environment(self, comprehensive_pact, api_client):
        """Test initialization with different environments."""
        # Test various initialization scenarios

        # Test alpha environment
        config = InitializeConfig(env="alpha", member="kr")
        assert config.env == "alpha"
        assert config.member == "kr"

        # Test with month parameter
        config_with_month = InitializeConfig(env="beta", member="us", month="2025-01")
        assert config_with_month.month == "2025-01"

        # Test initialization from config file
        import json
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "uuid": "TEST-UUID-001",
                "billing_group_id": "BG-TEST-001",
                "project_id": ["PROJ-001", "PROJ-002"],
                "campaign_id": ["CAMP-001"],
            }
            json.dump(config_data, f)
            config_file = f.name

        try:
            config_from_file = InitializeConfig(
                env="prod", member="eu", config_file=config_file
            )
            assert config_from_file.uuid == "TEST-UUID-001"
            assert config_from_file.billing_group_id == "BG-TEST-001"
            assert len(config_from_file.project_id) == 2
        finally:
            Path(config_file).unlink()

    def test_url_generation(self, comprehensive_pact, api_client):
        """Test URL generation for different environments."""
        # Test alpha URLs
        config = InitializeConfig(env="alpha", member="kr")
        urls = config.get_urls()
        assert "billing" in urls
        assert "payment" in urls

        # Test different members
        for member in ["kr", "jp", "us", "eu", "etc"]:
            config = InitializeConfig(env="alpha", member=member)
            member_urls = config.get_member_urls()
            assert len(member_urls) > 0

    def test_configuration_validation(self, comprehensive_pact, api_client):
        """Test configuration validation."""
        # Test invalid environment
        with pytest.raises(ValueError):
            InitializeConfig(env="invalid", member="kr")

        # Test invalid member
        with pytest.raises(ValueError):
            InitializeConfig(env="alpha", member="invalid")

        # Test month validation
        config = InitializeConfig(env="alpha", member="kr", month="2025-13")
        # Should handle invalid month gracefully
        assert config.month is not None

    def test_export_configuration(self, comprehensive_pact, api_client):
        """Test exporting configuration."""
        config = InitializeConfig(env="alpha", member="kr")

        # Test export to dict
        config_dict = config.to_dict()
        assert "env" in config_dict
        assert "member" in config_dict
        assert "uuid" in config_dict

        # Test export to JSON
        config_json = config.to_json()
        loaded = json.loads(config_json)
        assert loaded["env"] == "alpha"

        # Test saving to file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            config.save_to_file(output_file)
            with open(output_file) as f:
                saved_config = json.load(f)
            assert saved_config["env"] == "alpha"
        finally:
            Path(output_file).unlink()


@pytest.mark.contract
@pytest.mark.integration
class TestErrorHandlingContracts:
    """Contract tests for error handling across all managers."""

    def test_network_error_handling(self, comprehensive_pact, api_client):
        """Test handling of network errors."""
        # Simulate network error
        (
            comprehensive_pact.given("Network is unavailable")
            .upon_receiving("Request when network fails")
            .with_request("GET", "/api/v1/health")
            .will_respond_with(
                503,
                body={
                    "error": Like("SERVICE_UNAVAILABLE"),
                    "message": Like("Service temporarily unavailable"),
                },
            )
        )

        with comprehensive_pact:
            # Test various managers handle network errors gracefully
            adjustment_mgr = AdjustmentManager(month="2025-01", client=api_client)
            try:
                adjustment_mgr.get_adjustments(
                    adjustment_target=AdjustmentTarget.BILLING_GROUP, target_id="BG-001"
                )
            except Exception as e:
                assert "503" in str(e) or "SERVICE_UNAVAILABLE" in str(e)

    def test_validation_error_handling(self, comprehensive_pact, api_client):
        """Test handling of validation errors."""
        (
            comprehensive_pact.given("Validation is enforced")
            .upon_receiving("Request with invalid data")
            .with_request(
                "POST",
                "/api/v1/adjustments",
                headers={"Content-Type": "application/json"},
                body={
                    "adjustment_amount": -1000.0,  # Invalid negative amount
                    "adjustment_type": "INVALID_TYPE",
                    "month": "2025-01",
                },
            )
            .will_respond_with(
                400,
                body={
                    "error": Like("VALIDATION_ERROR"),
                    "message": Like("Invalid adjustment amount"),
                    "field": Like("adjustment_amount"),
                },
            )
        )

        with comprehensive_pact:
            adjustment_mgr = AdjustmentManager(month="2025-01", client=api_client)
            try:
                adjustment_mgr.apply_adjustment(
                    adjustment_amount=-1000.0,
                    adjustment_type="INVALID_TYPE",
                    adjustment_target=AdjustmentTarget.BILLING_GROUP,
                    target_id="BG-001",
                )
            except Exception as e:
                assert "400" in str(e) or "VALIDATION_ERROR" in str(e)
