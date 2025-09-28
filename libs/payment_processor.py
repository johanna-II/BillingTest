"""Payment Processor for complex payment processing logic."""

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .constants import PaymentStatus


class PaymentMethod(Enum):
    """Payment method types."""

    BANK_TRANSFER = "BANK_TRANSFER"
    CREDIT_CARD = "CREDIT_CARD"
    VIRTUAL_ACCOUNT = "VIRTUAL_ACCOUNT"
    DIRECT_DEBIT = "DIRECT_DEBIT"


class ProcessingStatus(Enum):
    """Payment processing status."""

    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    RETRY_NEEDED = "RETRY_NEEDED"


@dataclass
class PaymentRequest:
    """Payment request details."""

    payment_id: str
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    customer_id: str
    description: str
    metadata: Optional[Dict[str, str]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PaymentResult:
    """Payment processing result."""

    payment_id: str
    status: ProcessingStatus
    transaction_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    gateway_response: Optional[Dict] = None

    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == ProcessingStatus.COMPLETED

    @property
    def is_retriable(self) -> bool:
        """Check if payment can be retried."""
        return self.status in [
            ProcessingStatus.FAILED,
            ProcessingStatus.TIMEOUT,
            ProcessingStatus.RETRY_NEEDED,
        ]


@dataclass
class RetryPolicy:
    """Retry policy configuration."""

    max_attempts: int = 3
    initial_delay_seconds: int = 60
    backoff_multiplier: float = 2.0
    max_delay_seconds: int = 3600
    retriable_error_codes: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.retriable_error_codes is None:
            self.retriable_error_codes = [
                "TIMEOUT",
                "GATEWAY_ERROR",
                "NETWORK_ERROR",
                "TEMPORARY_FAILURE",
            ]


@dataclass
class ReconciliationRecord:
    """Payment reconciliation record."""

    payment_id: str
    internal_amount: Decimal
    gateway_amount: Decimal
    internal_status: PaymentStatus
    gateway_status: str
    discrepancy_type: Optional[str] = None
    discrepancy_amount: Optional[Decimal] = None

    @property
    def has_discrepancy(self) -> bool:
        """Check if there's a discrepancy."""
        return self.discrepancy_type is not None


class PaymentProcessor:
    """Handles complex payment processing logic.

    This class encapsulates payment processing workflows, reconciliation,
    retry logic, and gateway integration patterns.
    """

    # Standard payment processing fees by method
    PROCESSING_FEES = {
        PaymentMethod.BANK_TRANSFER: Decimal("0.001"),  # 0.1%
        PaymentMethod.CREDIT_CARD: Decimal("0.029"),  # 2.9%
        PaymentMethod.VIRTUAL_ACCOUNT: Decimal("0.005"),  # 0.5%
        PaymentMethod.DIRECT_DEBIT: Decimal("0.002"),  # 0.2%
    }

    # Fixed fees by method
    FIXED_FEES = {
        PaymentMethod.BANK_TRANSFER: Decimal("100"),  # 100 KRW
        PaymentMethod.CREDIT_CARD: Decimal("0"),  # No fixed fee
        PaymentMethod.VIRTUAL_ACCOUNT: Decimal("200"),  # 200 KRW
        PaymentMethod.DIRECT_DEBIT: Decimal("50"),  # 50 KRW
    }

    # Error codes that should trigger retry
    RETRIABLE_ERRORS = {
        "TIMEOUT",
        "GATEWAY_ERROR",
        "NETWORK_ERROR",
        "TEMPORARY_FAILURE",
        "RATE_LIMIT",
        "SERVICE_UNAVAILABLE",
    }

    @classmethod
    def calculate_processing_fee(
        cls, amount: Decimal, payment_method: PaymentMethod, include_tax: bool = True
    ) -> Dict[str, Decimal]:
        """Calculate payment processing fees.

        Args:
            amount: Payment amount
            payment_method: Payment method
            include_tax: Include VAT in calculation

        Returns:
            Dictionary with fee breakdown
        """
        # Get rates
        percentage_rate = cls.PROCESSING_FEES.get(payment_method, Decimal("0"))
        fixed_fee = cls.FIXED_FEES.get(payment_method, Decimal("0"))

        # Calculate percentage fee
        percentage_fee = amount * percentage_rate
        percentage_fee = percentage_fee.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Total fee before tax
        subtotal_fee = percentage_fee + fixed_fee

        # Calculate tax if needed
        tax_amount = Decimal("0")
        if include_tax:
            tax_amount = subtotal_fee * Decimal("0.1")  # 10% VAT
            tax_amount = tax_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Total fee
        total_fee = subtotal_fee + tax_amount

        return {
            "percentage_fee": percentage_fee,
            "fixed_fee": fixed_fee,
            "subtotal_fee": subtotal_fee,
            "tax_amount": tax_amount,
            "total_fee": total_fee,
            "net_amount": amount - total_fee,
        }

    @classmethod
    def calculate_retry_delay(
        cls, attempt_number: int, retry_policy: RetryPolicy
    ) -> int:
        """Calculate delay before next retry attempt.

        Args:
            attempt_number: Current attempt number (1-based)
            retry_policy: Retry policy configuration

        Returns:
            Delay in seconds before next retry
        """
        if attempt_number <= 0:
            return 0

        # Calculate exponential backoff
        delay = retry_policy.initial_delay_seconds * (
            retry_policy.backoff_multiplier ** (attempt_number - 1)
        )

        # Apply maximum delay cap
        delay = min(delay, retry_policy.max_delay_seconds)

        return int(delay)

    @classmethod
    def should_retry(
        cls,
        payment_result: PaymentResult,
        attempt_number: int,
        retry_policy: RetryPolicy,
    ) -> bool:
        """Determine if payment should be retried.

        Args:
            payment_result: Result from payment attempt
            attempt_number: Current attempt number
            retry_policy: Retry policy configuration

        Returns:
            True if payment should be retried
        """
        # Check if we've exceeded max attempts
        if attempt_number >= retry_policy.max_attempts:
            return False

        # Check if result is retriable
        if not payment_result.is_retriable:
            return False

        # Check if error code is retriable
        if payment_result.error_code and retry_policy.retriable_error_codes:
            return payment_result.error_code in retry_policy.retriable_error_codes

        # Default to retry for retriable statuses
        return True

    @classmethod
    def reconcile_payment(
        cls, internal_record: Dict[str, Any], gateway_record: Dict[str, Any]
    ) -> ReconciliationRecord:
        """Reconcile internal payment record with gateway record.

        Args:
            internal_record: Internal payment record
            gateway_record: Gateway payment record

        Returns:
            Reconciliation record with any discrepancies
        """
        payment_id = internal_record["payment_id"]
        internal_amount = Decimal(str(internal_record["amount"]))
        gateway_amount = Decimal(str(gateway_record["amount"]))
        internal_status = PaymentStatus(internal_record["status"])
        gateway_status = gateway_record["status"]

        # Check for discrepancies
        discrepancy_type = None
        discrepancy_amount = None

        # Amount discrepancy
        # Normalize decimals to avoid floating-point precision issues
        # This fixes the issue where amounts like 100.0 and 100.00 were treated as different
        # We use quantize to ensure both amounts have the same number of decimal places
        # ROUND_HALF_UP is used for consistent rounding behavior
        decimal_places = Decimal("0.01")  # 2 decimal places for currency
        internal_amount_normalized = internal_amount.quantize(
            decimal_places, rounding=ROUND_HALF_UP
        )
        gateway_amount_normalized = gateway_amount.quantize(
            decimal_places, rounding=ROUND_HALF_UP
        )

        if internal_amount_normalized != gateway_amount_normalized:
            discrepancy_type = "AMOUNT_MISMATCH"
            discrepancy_amount = abs(internal_amount - gateway_amount)

        # Status discrepancy
        elif not cls._is_status_match(internal_status, gateway_status):
            discrepancy_type = "STATUS_MISMATCH"

        return ReconciliationRecord(
            payment_id=payment_id,
            internal_amount=internal_amount,
            gateway_amount=gateway_amount,
            internal_status=internal_status,
            gateway_status=gateway_status,
            discrepancy_type=discrepancy_type,
            discrepancy_amount=discrepancy_amount,
        )

    @classmethod
    def _is_status_match(
        cls, internal_status: PaymentStatus, gateway_status: str
    ) -> bool:
        """Check if internal and gateway statuses match.

        Args:
            internal_status: Internal payment status
            gateway_status: Gateway payment status

        Returns:
            True if statuses are equivalent
        """
        # Map gateway statuses to internal statuses
        status_mapping = {
            "COMPLETED": PaymentStatus.PAID,
            "SUCCESS": PaymentStatus.PAID,
            "PAID": PaymentStatus.PAID,
            "PENDING": PaymentStatus.PENDING,
            "PROCESSING": PaymentStatus.REGISTERED,
            "CANCELLED": PaymentStatus.CANCELLED,
            "FAILED": PaymentStatus.FAILED,
            "REFUNDED": PaymentStatus.CANCELLED,
        }

        mapped_status = status_mapping.get(gateway_status.upper())
        return mapped_status == internal_status

    @classmethod
    def batch_reconcile(
        cls, internal_records: List[Dict], gateway_records: List[Dict]
    ) -> Dict[str, List[ReconciliationRecord]]:
        """Perform batch reconciliation.

        Args:
            internal_records: List of internal payment records
            gateway_records: List of gateway payment records

        Returns:
            Dictionary with matched, unmatched, and discrepancy records
        """
        # Create lookup maps
        internal_map = {r["payment_id"]: r for r in internal_records}
        gateway_map = {r["payment_id"]: r for r in gateway_records}

        matched = []
        discrepancies = []
        internal_only = []
        gateway_only = []

        # Process internal records
        for payment_id, internal_record in internal_map.items():
            if payment_id in gateway_map:
                # Reconcile matched records
                recon_record = cls.reconcile_payment(
                    internal_record, gateway_map[payment_id]
                )

                if recon_record.has_discrepancy:
                    discrepancies.append(recon_record)
                else:
                    matched.append(recon_record)
            else:
                # Internal record only
                internal_only.append(
                    ReconciliationRecord(
                        payment_id=payment_id,
                        internal_amount=Decimal(str(internal_record["amount"])),
                        gateway_amount=Decimal("0"),
                        internal_status=PaymentStatus(internal_record["status"]),
                        gateway_status="NOT_FOUND",
                        discrepancy_type="INTERNAL_ONLY",
                    )
                )

        # Process gateway-only records
        for payment_id, gateway_record in gateway_map.items():
            if payment_id not in internal_map:
                gateway_only.append(
                    ReconciliationRecord(
                        payment_id=payment_id,
                        internal_amount=Decimal("0"),
                        gateway_amount=Decimal(str(gateway_record["amount"])),
                        internal_status=PaymentStatus.UNKNOWN,
                        gateway_status=gateway_record["status"],
                        discrepancy_type="GATEWAY_ONLY",
                    )
                )

        return {
            "matched": matched,
            "discrepancies": discrepancies,
            "internal_only": internal_only,
            "gateway_only": gateway_only,
        }

    @classmethod
    def simulate_payment_processing(
        cls,
        payment_request: PaymentRequest,
        success_rate: float = 0.95,
        processing_time_ms: int = 2000,
    ) -> PaymentResult:
        """Simulate payment processing (for testing).

        Args:
            payment_request: Payment request details
            success_rate: Probability of success (0-1)
            processing_time_ms: Simulated processing time

        Returns:
            Simulated payment result
        """
        import random
        import time

        # Simulate processing delay
        time.sleep(processing_time_ms / 1000.0)

        # Determine success/failure
        is_success = random.random() < success_rate

        if is_success:
            return PaymentResult(
                payment_id=payment_request.payment_id,
                status=ProcessingStatus.COMPLETED,
                transaction_id=f"TXN-{payment_request.payment_id}",
                processed_at=datetime.now(),
                gateway_response={"status": "SUCCESS", "code": "00"},
            )
        else:
            # Simulate various failure scenarios
            failure_scenarios = [
                (ProcessingStatus.FAILED, "INSUFFICIENT_FUNDS", "Insufficient funds"),
                (ProcessingStatus.FAILED, "INVALID_CARD", "Invalid card number"),
                (ProcessingStatus.TIMEOUT, "TIMEOUT", "Gateway timeout"),
                (ProcessingStatus.RETRY_NEEDED, "NETWORK_ERROR", "Network error"),
            ]

            scenario = random.choice(failure_scenarios)
            return PaymentResult(
                payment_id=payment_request.payment_id,
                status=scenario[0],
                error_code=scenario[1],
                error_message=scenario[2],
                processed_at=datetime.now(),
            )

    @classmethod
    def validate_payment_request(
        cls, payment_request: PaymentRequest
    ) -> Tuple[bool, Optional[str]]:
        """Validate payment request.

        Args:
            payment_request: Payment request to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check amount
        if payment_request.amount <= 0:
            return False, "Amount must be positive"

        # Check currency
        valid_currencies = ["KRW", "USD", "EUR", "JPY"]
        if payment_request.currency not in valid_currencies:
            return False, f"Invalid currency: {payment_request.currency}"

        # Check payment method specific validations
        if payment_request.payment_method == PaymentMethod.CREDIT_CARD:
            # Would validate card details here
            pass
        elif payment_request.payment_method == PaymentMethod.BANK_TRANSFER:
            # Would validate bank account details here
            pass

        # Check for required metadata
        if payment_request.payment_method == PaymentMethod.VIRTUAL_ACCOUNT:
            if (
                not payment_request.metadata
                or "bank_code" not in payment_request.metadata
            ):
                return False, "Bank code required for virtual account"

        return True, None

    @classmethod
    def format_payment_amount(
        cls, amount: Decimal, currency: str, include_symbol: bool = True
    ) -> str:
        """Format payment amount for display.

        Args:
            amount: Payment amount
            currency: Currency code
            include_symbol: Include currency symbol

        Returns:
            Formatted amount string
        """
        # Currency symbols
        symbols = {"KRW": "₩", "USD": "$", "EUR": "€", "JPY": "¥"}

        # Format based on currency
        if currency == "KRW" or currency == "JPY":
            # No decimal places for KRW/JPY
            formatted = f"{int(amount):,}"
        else:
            # 2 decimal places for others
            formatted = f"{amount:,.2f}"

        # Add symbol if requested
        if include_symbol and currency in symbols:
            return f"{symbols[currency]}{formatted}"

        return f"{formatted} {currency}"
