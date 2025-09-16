"""Type definitions for the billing test suite."""

from __future__ import annotations

from typing import Any, TypedDict


class LocaleDescription(TypedDict):
    """Locale-specific description."""

    locale: str
    message: str


class AdjustmentData(TypedDict, total=False):
    """Data structure for billing adjustments."""

    adjustment: int | float
    adjustmentTypeCode: str
    descriptions: list[LocaleDescription]
    monthFrom: str
    monthTo: str
    adjustmentId: str | None
    billingGroupId: str | None
    projectId: str | None


class MeteringData(TypedDict):
    """Data structure for metering information."""

    appKey: str
    counterName: str
    counterType: str
    counterUnit: str
    counterVolume: str
    parentResourceId: str
    resourceId: str
    resourceName: str
    source: str
    timestamp: str


class MeteringRequest(TypedDict):
    """Request structure for metering API."""

    meterList: list[MeteringData]


class CreditData(TypedDict, total=False):
    """Data structure for credit operations."""

    creditName: str
    credit: int
    expirationDateFrom: str | None
    expirationDateTo: str | None
    expirationPeriod: int
    creditPayTargetData: str | None
    emailList: list[str]
    uuidList: list[str]


class PaymentData(TypedDict):
    """Data structure for payment operations."""

    paymentGroupId: str


class ContractData(TypedDict):
    """Data structure for contract operations."""

    contractId: str
    defaultYn: str
    monthFrom: str
    name: str


class BatchRequestData(TypedDict):
    """Data structure for batch operations."""

    is_async: str
    batchJobCode: str
    date: str


class APIResponse(TypedDict):
    """Standard API response structure."""

    header: dict[str, Any]
    data: dict[str, Any] | None


class BillingConfig(TypedDict):
    """Configuration for billing test environment."""

    uuid: str
    billing_group_id: str
    project_id: list[str]
    appkey: list[str]
    campaign_id: list[str]
    give_campaign_id: list[str]
    paid_campaign_id: list[str]
