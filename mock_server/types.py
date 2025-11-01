"""Type definitions for mock billing server.

This module provides TypedDict definitions for improved type safety
and better IDE support.
"""

from __future__ import annotations

from typing import TypedDict


class UsageItem(TypedDict, total=False):
    """Usage/metering item structure."""

    counterVolume: float
    counterName: str
    counterUnit: str
    counterType: str
    resourceId: str
    resourceName: str
    projectId: str
    appKey: str
    uuid: str


class CreditItem(TypedDict, total=False):
    """Credit item structure."""

    amount: int
    type: str  # PROMOTIONAL, FREE, PAID
    campaignId: str
    name: str
    creditCode: str
    expireDate: str
    restAmount: int


class AdjustmentItem(TypedDict, total=False):
    """Adjustment item structure."""

    type: str  # DISCOUNT, SURCHARGE
    method: str  # FIXED, RATE
    value: float
    description: str
    level: str  # PROJECT, BILLING_GROUP
    targetProjectId: str
    month: str
    adjustmentType: str
    adjustmentValue: float


class BillingRequest(TypedDict, total=False):
    """Billing calculation request structure."""

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
    """Line item in billing statement."""

    id: str
    counterName: str
    counterType: str
    unit: str
    quantity: float
    unitPrice: int
    amount: int
    resourceId: str
    resourceName: str
    projectId: str
    appKey: str
