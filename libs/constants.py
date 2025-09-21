"""Constants used throughout the billing test suite."""

from __future__ import annotations

from enum import StrEnum


class BatchJobCode(StrEnum):
    """Batch job codes for billing operations."""

    API_CALCULATE_USAGE_AND_PRICE = "API_CALCULATE_USAGE_AND_PRICE"
    BATCH_GENERATE_STATEMENT = "BATCH_GENERATE_STATEMENT"
    BATCH_PROCESS_PAYMENT = "BATCH_PROCESS_PAYMENT"
    BATCH_CREDIT_EXPIRY = "BATCH_CREDIT_EXPIRY"
    BATCH_CONTRACT_RENEWAL = "BATCH_CONTRACT_RENEWAL"


class AdjustmentType(StrEnum):
    """Types of billing adjustments."""

    FIXED_DISCOUNT = "FIXED_DISCOUNT"
    RATE_DISCOUNT = "RATE_DISCOUNT"
    FIXED_SURCHARGE = "FIXED_SURCHARGE"
    RATE_SURCHARGE = "RATE_SURCHARGE"


class AdjustmentTarget(StrEnum):
    """Targets for billing adjustments."""

    BILLING_GROUP = "BillingGroup"
    PROJECT = "Project"


class PaymentStatus(StrEnum):
    """Payment status codes."""

    READY = "READY"
    REGISTERED = "REGISTERED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class CreditType(StrEnum):
    """Types of credits."""

    FREE = "FREE"
    PAID = "PAID"


class CounterType(StrEnum):
    """Types of metering counters."""

    DELTA = "DELTA"
    GAUGE = "GAUGE"


class MemberCountry(StrEnum):
    """Member country codes."""

    KR = "kr"
    JP = "jp"
    ETC = "etc"


class ContractType(StrEnum):
    """Contract types for billing."""
    
    VOLUME = "VOLUME"
    PERIOD = "PERIOD"
    COMMITMENT = "COMMITMENT"
    PARTNER = "PARTNER"


class DiscountType(StrEnum):
    """Discount types for contracts."""
    
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


# Default values
DEFAULT_LOCALE = "ko_KR"
DEFAULT_TIMEOUT = 60
DEFAULT_RETRY_COUNT = 3
DEFAULT_CHECK_INTERVAL = 3
DEFAULT_PAGE_SIZE = 50

# API response headers
HEADER_SUCCESS_KEY = "isSuccessful"
HEADER_MESSAGE_KEY = "resultMessage"

# Date format
DATE_FORMAT = "%Y-%m"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
