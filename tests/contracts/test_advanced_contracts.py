"""Advanced contract tests for specific methods to maximize code coverage."""

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
)
from libs.Contract import ContractManager
from libs.Credit import CreditManager
from libs.exceptions import (
    AuthenticationException,
    ConflictException,
    InsufficientCreditException,
    NetworkException,
    PaymentRequiredException,
    RateLimitException,
    ResourceNotFoundException,
    ServerException,
    TimeoutException,
    ValidationException,
)
from libs.http_client import BillingAPIClient
from libs.Metering import MeteringManager
from libs.payment_api_client import PaymentAPIClient
from libs.Payments import PaymentManager

# Pact configuration
PACT_DIR = os.path.join(os.path.dirname(__file__), "pacts")
os.makedirs(PACT_DIR, exist_ok=True)


@pytest.fixture(scope="session")
def advanced_pact():
    """Set up advanced Pact consumer."""
    consumer = Consumer("BillingTestAdvanced")
    provider = Provider("BillingAPIAdvanced")

    pact = consumer.has_pact_with(provider, pact_dir=PACT_DIR)

    pact.start_service()
    yield pact
    pact.stop_service()


@pytest.fixture
def billing_client(advanced_pact):
    """Create Billing API client for pact testing."""
    return BillingAPIClient(base_url=f"http://localhost:{advanced_pact.port}/api/v1")


@pytest.fixture
def payment_client(advanced_pact):
    """Create Payment API client for pact testing."""
    return PaymentAPIClient(
        base_url=f"http://localhost:{advanced_pact.port}/payment/api/v1"
    )


@pytest.mark.contract
@pytest.mark.integration
class TestAdjustmentAdvancedContracts:
    """Advanced tests for AdjustmentManager uncovered methods."""

    def test_adjustment_with_all_targets(self, advanced_pact, billing_client):
        """Test adjustments for all target types."""
        targets = [
            (AdjustmentTarget.BILLING_GROUP, "BG-001"),
            (AdjustmentTarget.PROJECT, "PROJ-001"),
            (AdjustmentTarget.USER, "USER-001"),
            (AdjustmentTarget.CONTRACT, "CONTRACT-001"),
            (AdjustmentTarget.SERVICE, "SERVICE-001"),
        ]

        for target_type, target_id in targets:
            expected = {
                "adjustmentId": Term(r"[A-Z0-9-]+", f"ADJ-{target_type.value}"),
                "status": Like("SUCCESS"),
                "target": Like(target_type.value),
                "targetId": Like(target_id),
            }

            (
                advanced_pact.given(f"{target_type.value} exists")
                .upon_receiving(f"Request to apply adjustment to {target_type.value}")
                .with_request(
                    "POST",
                    "/api/v1/adjustments",
                    headers={"Content-Type": "application/json"},
                    body={
                        "adjustment_amount": 500.0,
                        "adjustment_type": "FIXED_SURCHARGE",
                        "adjustment_target": target_type.value,
                        "target_id": target_id,
                        "month": "2025-01",
                    },
                )
                .will_respond_with(200, body=expected)
            )

            with advanced_pact:
                manager = AdjustmentManager(month="2025-01", client=billing_client)
                result = manager.apply_adjustment(
                    adjustment_amount=500.0,
                    adjustment_type=AdjustmentType.FIXED_SURCHARGE,
                    adjustment_target=target_type,
                    target_id=target_id,
                )
                assert result.get("status") == "SUCCESS"

    def test_bulk_adjustments(self, advanced_pact, billing_client):
        """Test bulk adjustment operations."""
        expected = {
            "bulkId": Term(r"[A-Z0-9-]+", "BULK-ADJ-001"),
            "processed": Like(10),
            "failed": Like(0),
            "results": Like(
                [{"adjustmentId": Like("ADJ-001"), "status": Like("SUCCESS")}]
            ),
        }

        (
            advanced_pact.given("Bulk adjustment is supported")
            .upon_receiving("Request for bulk adjustments")
            .with_request(
                "POST",
                "/api/v1/adjustments/bulk",
                headers={"Content-Type": "application/json"},
                body={
                    "adjustments": Like(
                        [
                            {
                                "adjustment_amount": 100.0,
                                "adjustment_type": "FIXED_DISCOUNT",
                                "adjustment_target": "PROJECT",
                                "target_id": "PROJ-001",
                            }
                        ]
                    ),
                    "month": "2025-01",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = AdjustmentManager(month="2025-01", client=billing_client)
            # Test bulk operation
            adjustments = [
                {
                    "adjustment_amount": 100.0,
                    "adjustment_type": AdjustmentType.FIXED_DISCOUNT,
                    "adjustment_target": AdjustmentTarget.PROJECT,
                    "target_id": f"PROJ-{i:03d}",
                }
                for i in range(10)
            ]
            result = manager.apply_bulk_adjustments(adjustments)
            assert result.get("processed") == 10

    def test_adjustment_validation(self, advanced_pact, billing_client):
        """Test adjustment validation before applying."""
        expected = {
            "valid": Like(True),
            "warnings": Like([]),
            "estimatedImpact": Like(-1000.0),
        }

        (
            advanced_pact.given("Validation endpoint exists")
            .upon_receiving("Request to validate adjustment")
            .with_request(
                "POST",
                "/api/v1/adjustments/validate",
                headers={"Content-Type": "application/json"},
                body={
                    "adjustment_amount": 1000.0,
                    "adjustment_type": "FIXED_DISCOUNT",
                    "adjustment_target": "BILLING_GROUP",
                    "target_id": "BG-001",
                    "month": "2025-01",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = AdjustmentManager(month="2025-01", client=billing_client)
            result = manager.validate_adjustment(
                adjustment_amount=1000.0,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
                target_id="BG-001",
            )
            assert result.get("valid") is True


@pytest.mark.contract
@pytest.mark.integration
class TestBatchAdvancedContracts:
    """Advanced tests for BatchManager uncovered methods."""

    def test_all_batch_job_types(self, advanced_pact, billing_client):
        """Test all batch job types."""
        job_types = [
            BatchJobCode.BATCH_CREDIT_EXPIRY,
            BatchJobCode.BATCH_PAYMENT_CALCULATION,
            BatchJobCode.BATCH_GENERATE_STATEMENT,
            BatchJobCode.BATCH_USAGE_AGGREGATION,
            BatchJobCode.BATCH_CONTRACT_RENEWAL,
            BatchJobCode.BATCH_ADJUSTMENT_PROCESSING,
        ]

        for job_type in job_types:
            expected = {
                "batchId": Term(r"[A-Z0-9-]+", f"BATCH-{job_type.value}"),
                "jobCode": Like(job_type.value),
                "status": Like("QUEUED"),
                "estimatedDuration": Like(300),
            }

            (
                advanced_pact.given(f"Batch job {job_type.value} is available")
                .upon_receiving(f"Request to start {job_type.value}")
                .with_request(
                    "POST",
                    "/api/v1/batch/jobs",
                    headers={"Content-Type": "application/json"},
                    body={
                        "job_code": job_type.value,
                        "month": "2025-01",
                        "execution_day": 1,
                    },
                )
                .will_respond_with(200, body=expected)
            )

            with advanced_pact:
                manager = BatchManager(month="2025-01", client=billing_client)
                result = manager.request_batch_job(job_type)
                assert "batchId" in result

    def test_batch_job_cancellation(self, advanced_pact, billing_client):
        """Test cancelling batch jobs."""
        expected = {
            "status": Like("CANCELLED"),
            "batchId": Like("BATCH-001"),
            "cancelledAt": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:00:00"
            ),
        }

        (
            advanced_pact.given("Running batch job exists")
            .upon_receiving("Request to cancel batch job")
            .with_request(
                "POST",
                "/api/v1/batch/jobs/BATCH-001/cancel",
                headers={"Content-Type": "application/json"},
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = BatchManager(month="2025-01", client=billing_client)
            result = manager.cancel_batch_job("BATCH-001")
            assert result.get("status") == "CANCELLED"

    def test_batch_job_retry(self, advanced_pact, billing_client):
        """Test retrying failed batch jobs."""
        expected = {
            "newBatchId": Term(r"[A-Z0-9-]+", "BATCH-002"),
            "originalBatchId": Like("BATCH-001"),
            "status": Like("QUEUED"),
            "retryCount": Like(1),
        }

        (
            advanced_pact.given("Failed batch job exists")
            .upon_receiving("Request to retry batch job")
            .with_request(
                "POST",
                "/api/v1/batch/jobs/BATCH-001/retry",
                headers={"Content-Type": "application/json"},
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = BatchManager(month="2025-01", client=billing_client)
            result = manager.retry_batch_job("BATCH-001")
            assert "newBatchId" in result


@pytest.mark.contract
@pytest.mark.integration
class TestCalculationAdvancedContracts:
    """Advanced tests for CalculationManager uncovered methods."""

    def test_calculation_with_filters(self, advanced_pact, billing_client):
        """Test calculation with various filters."""
        expected = {
            "status": Like("COMPLETED"),
            "calculationId": Term(r"[A-Z0-9-]+", "CALC-001"),
            "filters": {
                "projects": Like(["PROJ-001", "PROJ-002"]),
                "services": Like(["compute", "storage"]),
                "excluded": Like([]),
            },
            "results": {"totalAmount": Like(5000.0), "itemCount": Like(25)},
        }

        (
            advanced_pact.given("Filtered calculation is supported")
            .upon_receiving("Request for filtered calculation")
            .with_request(
                "POST",
                "/api/v1/calculations/filtered",
                headers={"Content-Type": "application/json"},
                body={
                    "month": "2025-01",
                    "uuid": "UUID-001",
                    "filters": {
                        "projects": ["PROJ-001", "PROJ-002"],
                        "services": ["compute", "storage"],
                        "exclude_zero_usage": True,
                    },
                },
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = CalculationManager(
                month="2025-01", uuid="UUID-001", client=billing_client
            )
            result = manager.calculate_with_filters(
                projects=["PROJ-001", "PROJ-002"],
                services=["compute", "storage"],
                exclude_zero_usage=True,
            )
            assert result.get("status") == "COMPLETED"

    def test_incremental_calculation(self, advanced_pact, billing_client):
        """Test incremental calculation."""
        expected = {
            "status": Like("COMPLETED"),
            "mode": Like("INCREMENTAL"),
            "changedItems": Like(10),
            "totalItems": Like(100),
            "timeSaved": Like(240),  # seconds
        }

        (
            advanced_pact.given("Previous calculation exists")
            .upon_receiving("Request for incremental calculation")
            .with_request(
                "POST",
                "/api/v1/calculations/incremental",
                headers={"Content-Type": "application/json"},
                body={
                    "month": "2025-01",
                    "uuid": "UUID-001",
                    "since_timestamp": Like("2025-01-15T00:00:00"),
                },
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = CalculationManager(
                month="2025-01", uuid="UUID-001", client=billing_client
            )
            result = manager.incremental_calculation(
                since_timestamp="2025-01-15T00:00:00"
            )
            assert result.get("mode") == "INCREMENTAL"


@pytest.mark.contract
@pytest.mark.integration
class TestContractAdvancedContracts:
    """Advanced tests for ContractManager uncovered methods."""

    def test_contract_renewal(self, advanced_pact, billing_client):
        """Test contract renewal process."""
        expected = {
            "status": Like("RENEWED"),
            "oldContractId": Like("CONTRACT-001"),
            "newContractId": Term(r"[A-Z0-9-]+", "CONTRACT-002"),
            "renewalDate": Term(r"\d{4}-\d{2}-\d{2}", "2025-02-01"),
            "changes": Like([]),
        }

        (
            advanced_pact.given("Contract eligible for renewal")
            .upon_receiving("Request to renew contract")
            .with_request(
                "POST",
                "/api/v1/contracts/CONTRACT-001/renew",
                headers={"Content-Type": "application/json"},
                body={"billing_group_id": "BG-001", "renewal_month": "2025-02"},
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = ContractManager(
                month="2025-01", billing_group_id="BG-001", client=billing_client
            )
            result = manager.renew_contract(
                contract_id="CONTRACT-001", renewal_month="2025-02"
            )
            assert result.get("status") == "RENEWED"

    def test_contract_modification(self, advanced_pact, billing_client):
        """Test contract modification."""
        expected = {
            "status": Like("MODIFIED"),
            "contractId": Like("CONTRACT-001"),
            "modifications": Like(
                [
                    {
                        "field": Like("discount_rate"),
                        "oldValue": Like(5.0),
                        "newValue": Like(10.0),
                    }
                ]
            ),
            "effectiveDate": Term(r"\d{4}-\d{2}-\d{2}", "2025-01-15"),
        }

        (
            advanced_pact.given("Active contract exists")
            .upon_receiving("Request to modify contract")
            .with_request(
                "PATCH",
                "/api/v1/contracts/CONTRACT-001",
                headers={"Content-Type": "application/json"},
                body={
                    "modifications": {
                        "discount_rate": 10.0,
                        "additional_services": ["backup", "monitoring"],
                    },
                    "effective_date": "2025-01-15",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = ContractManager(
                month="2025-01", billing_group_id="BG-001", client=billing_client
            )
            result = manager.modify_contract(
                contract_id="CONTRACT-001",
                modifications={
                    "discount_rate": 10.0,
                    "additional_services": ["backup", "monitoring"],
                },
                effective_date="2025-01-15",
            )
            assert result.get("status") == "MODIFIED"

    def test_contract_termination(self, advanced_pact, billing_client):
        """Test contract termination."""
        expected = {
            "status": Like("TERMINATED"),
            "contractId": Like("CONTRACT-001"),
            "terminationDate": Term(r"\d{4}-\d{2}-\d{2}", "2025-01-31"),
            "finalInvoice": {
                "amount": Like(2500.0),
                "dueDate": Term(r"\d{4}-\d{2}-\d{2}", "2025-02-15"),
            },
        }

        (
            advanced_pact.given("Active contract exists")
            .upon_receiving("Request to terminate contract")
            .with_request(
                "POST",
                "/api/v1/contracts/CONTRACT-001/terminate",
                headers={"Content-Type": "application/json"},
                body={"termination_date": "2025-01-31", "reason": "Customer request"},
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = ContractManager(
                month="2025-01", billing_group_id="BG-001", client=billing_client
            )
            result = manager.terminate_contract(
                contract_id="CONTRACT-001",
                termination_date="2025-01-31",
                reason="Customer request",
            )
            assert result.get("status") == "TERMINATED"


@pytest.mark.contract
@pytest.mark.integration
class TestMeteringAdvancedContracts:
    """Advanced tests for MeteringManager uncovered methods."""

    def test_metering_aggregation(self, advanced_pact, billing_client):
        """Test metering data aggregation."""
        expected = {
            "aggregation": {
                "period": {
                    "start": Term(r"\d{4}-\d{2}-\d{2}", "2025-01-01"),
                    "end": Term(r"\d{4}-\d{2}-\d{2}", "2025-01-31"),
                },
                "byCounter": Like(
                    {
                        "compute.cpu.hours": {
                            "total": Like(74400.0),
                            "average": Like(100.0),
                            "max": Like(200.0),
                            "min": Like(50.0),
                        }
                    }
                ),
                "byApp": Like(
                    {
                        "APP-001": {
                            "totalVolume": Like(37200.0),
                            "counters": Like(["compute.cpu.hours", "storage.gb.hours"]),
                        }
                    }
                ),
            }
        }

        (
            advanced_pact.given("Metering data exists for aggregation")
            .upon_receiving("Request for metering aggregation")
            .with_request(
                "GET",
                "/api/v1/metering/aggregate",
                query={"month": "2025-01", "group_by": "counter,app"},
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = MeteringManager(month="2025-01", client=billing_client)
            result = manager.get_metering_aggregation(group_by=["counter", "app"])
            assert "aggregation" in result

    def test_metering_validation(self, advanced_pact, billing_client):
        """Test metering data validation."""
        expected = {
            "valid": Like(True),
            "warnings": Like(
                [
                    {
                        "type": Like("HIGH_USAGE"),
                        "message": Like("Usage 200% above average"),
                        "counter": Like("compute.cpu.hours"),
                    }
                ]
            ),
            "errors": Like([]),
        }

        (
            advanced_pact.given("Validation rules exist")
            .upon_receiving("Request to validate metering data")
            .with_request(
                "POST",
                "/api/v1/metering/validate",
                headers={"Content-Type": "application/json"},
                body={
                    "app_key": "APP-001",
                    "counter_name": "compute.cpu.hours",
                    "counter_type": "DELTA",
                    "counter_unit": "HOURS",
                    "counter_volume": "2000",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = MeteringManager(month="2025-01", client=billing_client)
            result = manager.validate_metering(
                app_key="APP-001",
                counter_name="compute.cpu.hours",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume="2000",
            )
            assert result.get("valid") is True

    def test_metering_correction(self, advanced_pact, billing_client):
        """Test metering data correction."""
        expected = {
            "correctionId": Term(r"[A-Z0-9-]+", "CORR-001"),
            "originalValue": Like("1000"),
            "correctedValue": Like("100"),
            "reason": Like("Data entry error"),
            "appliedAt": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-15T10:00:00"
            ),
        }

        (
            advanced_pact.given("Metering record exists")
            .upon_receiving("Request to correct metering data")
            .with_request(
                "POST",
                "/api/v1/metering/correct",
                headers={"Content-Type": "application/json"},
                body={
                    "metering_id": "METER-001",
                    "corrected_volume": "100",
                    "reason": "Data entry error",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = MeteringManager(month="2025-01", client=billing_client)
            result = manager.correct_metering(
                metering_id="METER-001",
                corrected_volume="100",
                reason="Data entry error",
            )
            assert "correctionId" in result


@pytest.mark.contract
@pytest.mark.integration
class TestPaymentAdvancedContracts:
    """Advanced tests for PaymentManager uncovered methods."""

    def test_payment_retry_with_strategy(self, advanced_pact, billing_client):
        """Test payment retry with different strategies."""
        expected = {
            "status": Like("RETRY_SCHEDULED"),
            "retryStrategy": Like("EXPONENTIAL_BACKOFF"),
            "nextRetryAt": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-16T10:00:00"
            ),
            "retryCount": Like(2),
            "maxRetries": Like(5),
        }

        (
            advanced_pact.given("Failed payment exists")
            .upon_receiving("Request to retry payment with strategy")
            .with_request(
                "POST",
                "/api/v1/payments/PG-001/retry",
                headers={"Content-Type": "application/json"},
                body={
                    "retry_strategy": "EXPONENTIAL_BACKOFF",
                    "max_retries": 5,
                    "initial_delay": 3600,
                },
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = PaymentManager(
                month="2025-01", uuid="UUID-001", client=billing_client
            )
            result = manager.schedule_payment_retry(
                payment_group_id="PG-001",
                retry_strategy="EXPONENTIAL_BACKOFF",
                max_retries=5,
            )
            assert result.get("status") == "RETRY_SCHEDULED"

    def test_payment_split(self, advanced_pact, billing_client):
        """Test splitting payment into installments."""
        expected = {
            "status": Like("SPLIT_CREATED"),
            "originalPaymentId": Like("PG-001"),
            "installments": Like(
                [
                    {
                        "installmentId": Term(r"[A-Z0-9-]+", "INST-001"),
                        "amount": Like(1000.0),
                        "dueDate": Term(r"\d{4}-\d{2}-\d{2}", "2025-02-01"),
                    }
                ]
            ),
            "totalInstallments": Like(3),
        }

        (
            advanced_pact.given("Payment can be split")
            .upon_receiving("Request to split payment")
            .with_request(
                "POST",
                "/api/v1/payments/PG-001/split",
                headers={"Content-Type": "application/json"},
                body={"installments": 3, "interval": "monthly"},
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = PaymentManager(
                month="2025-01", uuid="UUID-001", client=billing_client
            )
            result = manager.split_payment(
                payment_group_id="PG-001", installments=3, interval="monthly"
            )
            assert result.get("totalInstallments") == 3

    def test_payment_dispute(self, advanced_pact, billing_client):
        """Test payment dispute handling."""
        expected = {
            "disputeId": Term(r"[A-Z0-9-]+", "DISPUTE-001"),
            "paymentId": Like("PG-001"),
            "status": Like("UNDER_REVIEW"),
            "reason": Like("Incorrect charge"),
            "createdAt": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-15T10:00:00"
            ),
        }

        (
            advanced_pact.given("Payment exists")
            .upon_receiving("Request to dispute payment")
            .with_request(
                "POST",
                "/api/v1/payments/PG-001/dispute",
                headers={"Content-Type": "application/json"},
                body={
                    "reason": "Incorrect charge",
                    "disputed_amount": 500.0,
                    "evidence": ["receipt-001.pdf"],
                },
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = PaymentManager(
                month="2025-01", uuid="UUID-001", client=billing_client
            )
            result = manager.dispute_payment(
                payment_group_id="PG-001",
                reason="Incorrect charge",
                disputed_amount=500.0,
                evidence=["receipt-001.pdf"],
            )
            assert "disputeId" in result


@pytest.mark.contract
@pytest.mark.integration
class TestCreditAdvancedContracts:
    """Advanced tests for CreditManager uncovered methods."""

    def test_credit_transfer(self, advanced_pact, billing_client):
        """Test credit transfer between users."""
        expected = {
            "transferId": Term(r"[A-Z0-9-]+", "TRANSFER-001"),
            "status": Like("COMPLETED"),
            "fromUser": Like("UUID-001"),
            "toUser": Like("UUID-002"),
            "amount": Like(500.0),
            "remainingBalance": Like(1500.0),
        }

        (
            advanced_pact.given("Both users exist with credits")
            .upon_receiving("Request to transfer credit")
            .with_request(
                "POST",
                "/api/v1/credits/transfer",
                headers={"Content-Type": "application/json"},
                body={
                    "from_uuid": "UUID-001",
                    "to_uuid": "UUID-002",
                    "amount": 500.0,
                    "credit_type": "CAMPAIGN",
                },
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = CreditManager(uuid="UUID-001", client=billing_client)
            result = manager.transfer_credit(
                to_uuid="UUID-002", amount=500.0, credit_type=CreditType.CAMPAIGN
            )
            assert result.get("status") == "COMPLETED"

    def test_credit_expiry_extension(self, advanced_pact, billing_client):
        """Test extending credit expiry date."""
        expected = {
            "creditId": Like("CREDIT-001"),
            "status": Like("EXTENDED"),
            "oldExpiryDate": Term(r"\d{4}-\d{2}-\d{2}", "2025-02-01"),
            "newExpiryDate": Term(r"\d{4}-\d{2}-\d{2}", "2025-03-01"),
            "extensionDays": Like(30),
        }

        (
            advanced_pact.given("Credit near expiry exists")
            .upon_receiving("Request to extend credit expiry")
            .with_request(
                "POST",
                "/api/v1/credits/CREDIT-001/extend",
                headers={"Content-Type": "application/json"},
                body={"extension_days": 30, "reason": "Customer retention"},
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = CreditManager(uuid="UUID-001", client=billing_client)
            result = manager.extend_credit_expiry(
                credit_id="CREDIT-001", extension_days=30, reason="Customer retention"
            )
            assert result.get("status") == "EXTENDED"

    def test_credit_usage_report(self, advanced_pact, billing_client):
        """Test detailed credit usage report."""
        expected = {
            "report": {
                "period": {
                    "start": Term(r"\d{4}-\d{2}-\d{2}", "2025-01-01"),
                    "end": Term(r"\d{4}-\d{2}-\d{2}", "2025-01-31"),
                },
                "totalGranted": Like(10000.0),
                "totalUsed": Like(7500.0),
                "totalExpired": Like(500.0),
                "totalRemaining": Like(2000.0),
                "usageByType": Like(
                    {
                        "CAMPAIGN": Like(5000.0),
                        "REFUND": Like(2000.0),
                        "BONUS": Like(500.0),
                    }
                ),
                "topUsers": Like(
                    [
                        {
                            "uuid": Like("UUID-001"),
                            "used": Like(3000.0),
                            "percentage": Like(40.0),
                        }
                    ]
                ),
            }
        }

        (
            advanced_pact.given("Credit usage data exists")
            .upon_receiving("Request for credit usage report")
            .with_request(
                "GET",
                "/api/v1/credits/report",
                query={"start_date": "2025-01-01", "end_date": "2025-01-31"},
            )
            .will_respond_with(200, body=expected)
        )

        with advanced_pact:
            manager = CreditManager(uuid="UUID-001", client=billing_client)
            result = manager.get_credit_usage_report(
                start_date="2025-01-01", end_date="2025-01-31"
            )
            assert "report" in result


@pytest.mark.contract
@pytest.mark.integration
class TestExceptionHandlingContracts:
    """Test exception handling for all custom exceptions."""

    def test_all_exception_types(self, advanced_pact, billing_client):
        """Test handling of all custom exception types."""
        exceptions = [
            (401, AuthenticationException, "Invalid credentials"),
            (400, ValidationException, "Invalid input"),
            (429, RateLimitException, "Rate limit exceeded"),
            (500, ServerException, "Internal server error"),
            (503, NetworkException, "Network unavailable"),
            (504, TimeoutException, "Request timeout"),
            (404, ResourceNotFoundException, "Resource not found"),
            (409, ConflictException, "Resource conflict"),
            (402, PaymentRequiredException, "Payment required"),
            (403, InsufficientCreditException, "Insufficient credit"),
        ]

        for status_code, exception_class, message in exceptions:
            (
                advanced_pact.given("Error condition exists")
                .upon_receiving(f"Request triggering {exception_class.__name__}")
                .with_request("GET", f"/api/v1/test/error/{status_code}")
                .will_respond_with(
                    status_code,
                    body={
                        "error": Like(exception_class.__name__),
                        "message": Like(message),
                        "code": Like(status_code),
                    },
                )
            )

            with advanced_pact:
                try:
                    # Trigger the error
                    billing_client._request("GET", f"/test/error/{status_code}")
                except exception_class as e:
                    assert str(e) == message or message in str(e)
                except Exception as e:
                    # Some exceptions might be wrapped
                    assert status_code in str(e) or message in str(e)
