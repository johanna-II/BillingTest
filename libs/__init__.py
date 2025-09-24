"""Billing Test Suite Library.

This package provides utilities for automated billing system testing,
including metering, payments, credits, contracts, and adjustments.
"""

# Version info
__version__ = "0.2.0"
__author__ = "Billing Test Team"

# Import main classes for easier access
from .Adjustment import AdjustmentManager
from .Batch import BatchManager
from .Calculation import CalculationManager
from .constants import (
    AdjustmentTarget,
    AdjustmentType,
    BatchJobCode,
    CounterType,
    CreditType,
    MemberCountry,
    PaymentStatus,
)
from .Contract import ContractManager
from .Credit import CreditManager
from .exceptions import (
    APIRequestException,
    AuthenticationException,
    BillingTestException,
    ConfigurationException,
    DuplicateResourceException,
    ResourceNotFoundException,
    TimeoutException,
    ValidationException,
)
from .http_client import BillingAPIClient
from .InitializeConfig import ConfigurationManager, InitializeConfig
from .Metering import MeteringManager
from .Payments import PaymentManager

# Define public API
__all__ = [
    "APIRequestException",
    "AdjustmentManager",
    "AdjustmentTarget",
    "AdjustmentType",
    "AuthenticationException",
    "BatchJobCode",
    "BatchManager",
    "BillingAPIClient",
    "BillingTestException",
    "CalculationManager",
    "ConfigurationException",
    "ConfigurationManager",
    "ContractManager",
    "CounterType",
    "CreditManager",
    "CreditType",
    "DuplicateResourceException",
    "InitializeConfig",
    "MemberCountry",
    "MeteringManager",
    "PaymentManager",
    "PaymentStatus",
    "ResourceNotFoundException",
    "TimeoutException",
    "ValidationException",
]

# Legacy compatibility aliases
Adjustments = AdjustmentManager
Metering = MeteringManager
Calculation = CalculationManager
Payments = PaymentManager
Contract = ContractManager
Credit = CreditManager
Batch = BatchManager
