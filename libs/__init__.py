"""Billing Test Suite Library.

This package provides utilities for automated billing system testing,
including metering, payments, credits, contracts, and adjustments.
"""

# Version info
__version__ = "0.2.0"
__author__ = "Billing Test Team"

# Import main classes for easier access
from .adjustment import AdjustmentManager, Adjustments
from .Batch import Batches, BatchManager
from .calculation import Calculation, CalculationManager
from .constants import (
    AdjustmentTarget,
    AdjustmentType,
    BatchJobCode,
    CounterType,
    CreditType,
    MemberCountry,
    PaymentStatus,
)
from .Contract import Contract, ContractManager
from .Credit import Credit, CreditManager
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
from .http_client import BillingAPIClient, SendDataSession
from .InitializeConfig import ConfigurationManager, InitializeConfig

# New managers
from .Metering import Metering, MeteringManager
from .Payments import PaymentManager, Payments

# Legacy imports for backward compatibility
from .SessionHandler import SendDataSession as SessionHandler

# Define public API
__all__ = [
    "APIRequestException",
    "AdjustmentManager",
    "AdjustmentTarget",
    "AdjustmentType",
    "Adjustments",
    "AuthenticationException",
    "BatchJobCode",
    "BatchManager",
    "Batches",
    "BillingAPIClient",
    "BillingTestException",
    "Calculation",
    "CalculationManager",
    "ConfigurationException",
    "ConfigurationManager",
    "Contract",
    "ContractManager",
    "CounterType",
    "Credit",
    "CreditManager",
    "CreditType",
    "DuplicateResourceException",
    "InitializeConfig",
    "MemberCountry",
    "Metering",
    "MeteringManager",
    "PaymentManager",
    "PaymentStatus",
    "Payments",
    "ResourceNotFoundException",
    "SendDataSession",
    "SessionHandler",
    "TimeoutException",
    "ValidationException",
]
