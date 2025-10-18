"""Constants and enumerations used throughout the billing test suite.

This module provides centralized definitions for all constants, enums,
and configuration values used in the billing system.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Final


# Enumerations
class BatchJobCode(StrEnum):
    """Batch job codes for billing operations."""

    API_CALCULATE_USAGE_AND_PRICE = "API_CALCULATE_USAGE_AND_PRICE"
    BATCH_GENERATE_STATEMENT = "BATCH_GENERATE_STATEMENT"
    BATCH_PROCESS_PAYMENT = "BATCH_PROCESS_PAYMENT"
    BATCH_CREDIT_EXPIRY = "BATCH_CREDIT_EXPIRY"
    BATCH_PAYMENT_REMINDER = "BATCH_PAYMENT_REMINDER"
    BATCH_SEND_INVOICE = "BATCH_SEND_INVOICE"
    BATCH_CONTRACT_RENEWAL = "BATCH_CONTRACT_RENEWAL"
    BATCH_RECONCILIATION = "BATCH_RECONCILIATION"
    BATCH_USAGE_AGGREGATION = "BATCH_USAGE_AGGREGATION"


class AdjustmentType(StrEnum):
    """Types of billing adjustments."""

    FIXED_DISCOUNT = "FIXED_DISCOUNT"
    RATE_DISCOUNT = "RATE_DISCOUNT"
    FIXED_SURCHARGE = "FIXED_SURCHARGE"
    RATE_SURCHARGE = "RATE_SURCHARGE"
    CREDIT_ADJUSTMENT = "CREDIT_ADJUSTMENT"
    TAX_ADJUSTMENT = "TAX_ADJUSTMENT"

    @property
    def is_discount(self) -> bool:
        """Check if this is a discount type."""
        return "DISCOUNT" in self.value

    @property
    def is_surcharge(self) -> bool:
        """Check if this is a surcharge type."""
        return "SURCHARGE" in self.value


class AdjustmentTarget(StrEnum):
    """Targets for billing adjustments."""

    BILLING_GROUP = "BillingGroup"
    PROJECT = "Project"
    CAMPAIGN = "Campaign"
    INVOICE = "Invoice"
    LINE_ITEM = "LineItem"


class PaymentStatus(StrEnum):
    """Payment status codes."""

    READY = "READY"
    REGISTERED = "REGISTERED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    REFUNDED = "REFUNDED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    UNKNOWN = "UNKNOWN"

    @property
    def is_final(self) -> bool:
        """Check if this is a final status."""
        return self in {
            PaymentStatus.PAID,
            PaymentStatus.CANCELLED,
            PaymentStatus.FAILED,
            PaymentStatus.REFUNDED,
        }

    @property
    def is_active(self) -> bool:
        """Check if this is an active status."""
        return self in {
            PaymentStatus.READY,
            PaymentStatus.REGISTERED,
            PaymentStatus.PENDING,
            PaymentStatus.PARTIALLY_PAID,
        }


class CreditType(StrEnum):
    """Types of credits."""

    FREE = "FREE"
    PAID = "PAID"
    PROMOTIONAL = "PROMOTIONAL"
    COMPENSATION = "COMPENSATION"
    CAMPAIGN = "CAMPAIGN"
    REFUND = "REFUND"
    BONUS = "BONUS"

    @property
    def requires_payment(self) -> bool:
        """Check if this credit type requires payment."""
        return self == CreditType.PAID


class CounterType(StrEnum):
    """Types of metering counters."""

    DELTA = "DELTA"
    GAUGE = "GAUGE"
    CUMULATIVE = "CUMULATIVE"

    @property
    def is_incremental(self) -> bool:
        """Check if this counter type is incremental."""
        return self in {CounterType.DELTA, CounterType.CUMULATIVE}


class MemberCountry(StrEnum):
    """Member country codes."""

    KR = "kr"
    JP = "jp"
    US = "us"
    EU = "eu"
    ETC = "etc"

    @property
    def display_name(self) -> str:
        """Get display name for the country."""
        names = {
            MemberCountry.KR: "Korea",
            MemberCountry.JP: "Japan",
            MemberCountry.US: "United States",
            MemberCountry.EU: "Europe",
            MemberCountry.ETC: "Other",
        }
        return names.get(self, self.value)


class ContractType(StrEnum):
    """Contract types for billing."""

    VOLUME = "VOLUME"
    PERIOD = "PERIOD"
    COMMITMENT = "COMMITMENT"
    PARTNER = "PARTNER"
    SUBSCRIPTION = "SUBSCRIPTION"
    PAY_AS_YOU_GO = "PAY_AS_YOU_GO"

    @property
    def has_commitment(self) -> bool:
        """Check if this contract type has commitment."""
        return self in {ContractType.COMMITMENT, ContractType.SUBSCRIPTION}


class DiscountType(StrEnum):
    """Discount types for contracts."""

    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"
    TIERED = "TIERED"
    VOLUME_BASED = "VOLUME_BASED"


class BillingCycle(StrEnum):
    """Billing cycle options."""

    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUALLY = "ANNUALLY"
    CUSTOM = "CUSTOM"

    @property
    def months(self) -> int:
        """Get number of months in the billing cycle."""
        cycle_months = {
            BillingCycle.MONTHLY: 1,
            BillingCycle.QUARTERLY: 3,
            BillingCycle.ANNUALLY: 12,
            BillingCycle.CUSTOM: 0,  # Variable
        }
        return cycle_months.get(self, 0)


class Currency(StrEnum):
    """Supported currencies."""

    USD = "USD"
    KRW = "KRW"
    JPY = "JPY"
    EUR = "EUR"

    @property
    def symbol(self) -> str:
        """Get currency symbol."""
        symbols = {
            Currency.USD: "$",
            Currency.KRW: "₩",
            Currency.JPY: "¥",
            Currency.EUR: "€",
        }
        return symbols.get(self, self.value)

    @property
    def decimal_places(self) -> int:
        """Get standard decimal places for the currency."""
        # JPY and KRW typically don't use decimal places
        return 0 if self in {Currency.JPY, Currency.KRW} else 2


# HTTP Status codes for specific handling
class HTTPStatus(IntEnum):
    """HTTP status codes with billing-specific handling."""

    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504

    @property
    def is_success(self) -> bool:
        """Check if this is a success status."""
        return 200 <= self < 300

    @property
    def is_client_error(self) -> bool:
        """Check if this is a client error."""
        return 400 <= self < 500

    @property
    def is_server_error(self) -> bool:
        """Check if this is a server error."""
        return 500 <= self < 600

    @property
    def is_retryable(self) -> bool:
        """Check if this status indicates a retryable error."""
        return self in {
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        }


# Configuration dataclasses
@dataclass(frozen=True)
class TimeoutConfig:
    """Timeout configuration values."""

    default: int = 60
    connect: int = 10
    read: int = 60
    write: int = 60
    api_call: int = 30
    batch_job: int = 300
    long_running: int = 600


@dataclass(frozen=True)
class RetryConfig:
    """Retry configuration values."""

    max_attempts: int = 10
    backoff_factor: float = 2.0
    max_backoff: int = 120
    status_codes: frozenset[int] = frozenset(
        {
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        }
    )


@dataclass(frozen=True)
class PaginationConfig:
    """Pagination configuration values."""

    default_page_size: int = 50
    max_page_size: int = 1000
    default_page: int = 1


# Default configurations
DEFAULT_TIMEOUT_CONFIG: Final = TimeoutConfig()
DEFAULT_RETRY_CONFIG: Final = RetryConfig()
DEFAULT_PAGINATION_CONFIG: Final = PaginationConfig()

# Simple constants
DEFAULT_LOCALE: Final[str] = "ko_KR"
DEFAULT_TIMEZONE: Final[str] = "Asia/Seoul"
DEFAULT_ENCODING: Final[str] = "utf-8"

# Legacy constants for backward compatibility
DEFAULT_TIMEOUT: Final[int] = DEFAULT_TIMEOUT_CONFIG.default
DEFAULT_RETRY_COUNT: Final[int] = DEFAULT_RETRY_CONFIG.max_attempts
DEFAULT_CHECK_INTERVAL: Final[int] = 3
DEFAULT_PAGE_SIZE: Final[int] = DEFAULT_PAGINATION_CONFIG.default_page_size

# API response headers
HEADER_SUCCESS_KEY: Final[str] = "isSuccessful"
HEADER_MESSAGE_KEY: Final[str] = "resultMessage"
HEADER_CODE_KEY: Final[str] = "resultCode"
HEADER_TRACE_ID_KEY: Final[str] = "traceId"

# Date and time formats
DATE_FORMAT: Final[str] = "%Y-%m"
DATE_FORMAT_FULL: Final[str] = "%Y-%m-%d"
DATETIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S.%f%z"
DATETIME_FORMAT_SHORT: Final[str] = "%Y-%m-%d %H:%M:%S"

# Validation patterns
MONTH_PATTERN: Final[str] = r"^\d{4}-\d{2}$"
UUID_PATTERN: Final[str] = (
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
)
EMAIL_PATTERN: Final[str] = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# Size limits
MAX_BATCH_SIZE: Final[int] = 1000
MAX_CREDIT_AMOUNT: Final[int] = 1_000_000_000  # 1 billion
MAX_ADJUSTMENT_PERCENTAGE: Final[float] = 100.0
MAX_RETRY_ATTEMPTS: Final[int] = 10

# Rate limiting
RATE_LIMIT_CALLS_PER_MINUTE: Final[int] = 60
RATE_LIMIT_CALLS_PER_HOUR: Final[int] = 1000

# Cache settings
CACHE_TTL_SECONDS: Final[int] = 300  # 5 minutes
CACHE_TTL_CONFIG: Final[int] = 3600  # 1 hour

# Feature flags
FEATURE_ASYNC_PROCESSING: Final[bool] = True
FEATURE_BULK_OPERATIONS: Final[bool] = True
FEATURE_ADVANCED_METRICS: Final[bool] = False

# Environment names
ENV_DEVELOPMENT: Final[str] = "development"
ENV_STAGING: Final[str] = "staging"
ENV_PRODUCTION: Final[str] = "production"
ENV_TEST: Final[str] = "test"

# Log levels
LOG_LEVEL_DEBUG: Final[str] = "DEBUG"
LOG_LEVEL_INFO: Final[str] = "INFO"
LOG_LEVEL_WARNING: Final[str] = "WARNING"
LOG_LEVEL_ERROR: Final[str] = "ERROR"
LOG_LEVEL_CRITICAL: Final[str] = "CRITICAL"
