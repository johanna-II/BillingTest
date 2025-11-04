"""Type definitions for mock billing server.

This module provides TypedDict definitions for improved type safety
and better IDE support.
"""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict


class UsageItem(TypedDict):
    """Usage/metering item structure.

    Matches TypeScript UsageItem interface with required/optional fields.
    """

    # Required fields
    counterVolume: float
    counterName: str
    counterUnit: str

    # Optional fields
    counterType: NotRequired[str]
    resourceId: NotRequired[str]
    resourceName: NotRequired[str]
    projectId: NotRequired[str]
    appKey: NotRequired[str]
    uuid: NotRequired[str]


class CreditItem(TypedDict):
    """Credit item structure.

    Matches TypeScript CreditItem interface.
    """

    # Required fields
    amount: int
    type: Literal["PROMOTIONAL", "FREE", "PAID"]

    # Optional fields
    campaignId: NotRequired[str]
    name: NotRequired[str]
    creditCode: NotRequired[str]
    expireDate: NotRequired[str]
    restAmount: NotRequired[int]


class AdjustmentItem(TypedDict):
    """Adjustment item structure.

    Matches TypeScript AdjustmentItem interface.
    """

    # Required fields
    type: Literal["DISCOUNT", "SURCHARGE"]
    method: Literal["FIXED", "RATE"]
    value: float

    # Optional fields
    description: NotRequired[str]
    level: NotRequired[str]  # PROJECT, BILLING_GROUP
    targetProjectId: NotRequired[str]
    month: NotRequired[str]

    # Legacy/alternate field names - these duplicate the required fields above.
    # Use adjustmentType instead of type and adjustmentValue instead of value
    # when interfacing with systems that expect these alternative field names.
    adjustmentType: NotRequired[str]
    adjustmentValue: NotRequired[float]


class BillingRequest(TypedDict, total=False):
    """Billing calculation request structure.

    All fields are optional as this is a request body.
    Matches TypeScript BillingRequest interface.
    """

    uuid: str
    billingGroupId: str
    targetDate: str
    month: str
    unpaidAmount: int
    isOverdue: bool
    usage: list[UsageItem]
    credits: list[CreditItem]
    adjustments: list[AdjustmentItem]


class LineItem(TypedDict):
    """Line item in billing statement.

    Matches TypeScript LineItem structure with required/optional fields.
    """

    # Required fields
    id: str
    counterName: str
    counterType: str
    unit: str
    quantity: float
    unitPrice: int
    amount: int

    # Optional fields (matching TypeScript UsageItem)
    resourceId: NotRequired[str]
    resourceName: NotRequired[str]
    projectId: NotRequired[str]
    appKey: NotRequired[str]
