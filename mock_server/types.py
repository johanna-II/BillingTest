"""Type definitions for mock billing server.

This module provides TypedDict definitions for improved type safety
and better IDE support.
"""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict, Union, cast


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
    """Modern adjustment item structure.

    Uses 'type' and 'value' fields with strict typing.
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


class LegacyAdjustmentItem(TypedDict):
    """Legacy adjustment item structure.

    Uses 'adjustmentType' and 'adjustmentValue' fields for backward compatibility
    with older systems that expect these field names.
    """

    # Required fields
    adjustmentType: str  # Should be "DISCOUNT" or "SURCHARGE"
    method: Literal["FIXED", "RATE"]
    adjustmentValue: float

    # Optional fields
    description: NotRequired[str]
    level: NotRequired[str]  # PROJECT, BILLING_GROUP
    targetProjectId: NotRequired[str]
    month: NotRequired[str]


# Union type to accept either modern or legacy format
AdjustmentItemInput = Union[AdjustmentItem, LegacyAdjustmentItem]


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


# Conversion helper functions


def normalize_adjustment_item(item: AdjustmentItemInput) -> AdjustmentItem:
    """Convert any adjustment item format to the modern format.

    Args:
        item: Either modern or legacy adjustment item

    Returns:
        Modern AdjustmentItem with 'type' and 'value' fields

    Examples:
        >>> legacy = {"adjustmentType": "DISCOUNT", "method": "FIXED", "adjustmentValue": 10.0}
        >>> modern = normalize_adjustment_item(legacy)
        >>> modern["type"]
        'DISCOUNT'
    """
    # Check if this is a legacy format (has adjustmentType)
    if "adjustmentType" in item:
        legacy = cast(LegacyAdjustmentItem, item)
        normalized: AdjustmentItem = {
            "type": cast(Literal["DISCOUNT", "SURCHARGE"], legacy["adjustmentType"]),
            "method": legacy["method"],
            "value": legacy["adjustmentValue"],
        }
        # Copy optional fields
        for key in ("description", "level", "targetProjectId", "month"):
            if key in legacy:
                normalized[key] = legacy[key]
        return normalized

    # Already modern format
    return item


def to_legacy_adjustment_item(item: AdjustmentItem) -> LegacyAdjustmentItem:
    """Convert modern adjustment item to legacy format.

    Args:
        item: Modern adjustment item

    Returns:
        Legacy AdjustmentItem with 'adjustmentType' and 'adjustmentValue' fields

    Examples:
        >>> modern = {"type": "DISCOUNT", "method": "FIXED", "value": 10.0}
        >>> legacy = to_legacy_adjustment_item(modern)
        >>> legacy["adjustmentType"]
        'DISCOUNT'
    """
    legacy: LegacyAdjustmentItem = {
        "adjustmentType": item["type"],
        "method": item["method"],
        "adjustmentValue": item["value"],
    }
    # Copy optional fields
    for key in ("description", "level", "targetProjectId", "month"):
        if key in item:
            legacy[key] = item[key]
    return legacy
