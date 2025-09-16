"""Adjustment management for billing system."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypedDict

from config import url

from .constants import DEFAULT_LOCALE, AdjustmentTarget, AdjustmentType
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient

if TYPE_CHECKING:
    from .types import AdjustmentData


class LegacyAdjustmentParams(TypedDict, total=False):
    """Legacy parameters for adjustment operations."""

    adjustment: float
    adjustmentType: str
    adjustmentTarget: str
    billingGroupId: str
    projectId: str
    billingGroupid: str  # Note: lowercase 'id' for backward compatibility


logger = logging.getLogger(__name__)


class AdjustmentManager:
    """Manages billing adjustments (discounts/surcharges)."""

    def __init__(self, month: str) -> None:
        """Initialize adjustment manager.

        Args:
            month: Target month in YYYY-MM format
        """
        self.month = month
        self._client = BillingAPIClient(url.BASE_BILLING_URL)

    def __repr__(self) -> str:
        """Return string representation of AdjustmentManager."""
        return f"AdjustmentManager(month={self.month})"

    def apply_adjustment(
        self,
        adjustment_amount: float,
        adjustment_type: AdjustmentType | str,
        adjustment_target: AdjustmentTarget | str,
        target_id: str,
        description: str = "QA billing automation test",
    ) -> dict[str, Any]:
        """Apply discount or surcharge to billing group or project.

        Args:
            adjustment_amount: Amount or percentage of adjustment
            adjustment_type: Type of adjustment (FIXED_DISCOUNT, RATE_DISCOUNT, etc.)
            adjustment_target: Target type (BillingGroup or Project)
            target_id: ID of the target (billing group ID or project ID)
            description: Description of the adjustment

        Returns:
            API response data

        Raises:
            ValidationException: If parameters are invalid
            APIRequestException: If API request fails
        """
        # Validate and normalize parameters
        adjustment_type_str = (
            adjustment_type.value
            if isinstance(adjustment_type, AdjustmentType)
            else adjustment_type
        )
        adjustment_target_str = (
            adjustment_target.value
            if isinstance(adjustment_target, AdjustmentTarget)
            else adjustment_target
        )

        if adjustment_target_str not in [t.value for t in AdjustmentTarget]:
            error_msg = f"Invalid adjustment target: {adjustment_target_str}"
            raise ValidationException(error_msg)

        # Build request data
        adjustment_data: AdjustmentData = {  # type: ignore[misc]
            "adjustment": adjustment_amount,
            "adjustmentTypeCode": adjustment_type_str,
            "descriptions": [{"locale": DEFAULT_LOCALE, "message": description}],
            "monthFrom": self.month,
            "monthTo": self.month,
            "adjustmentId": None,
            "billingGroupId": None,
            "projectId": None,
        }

        # Set target-specific fields and endpoint
        if adjustment_target_str == AdjustmentTarget.BILLING_GROUP.value:
            endpoint = "billing/admin/billing-groups/adjustments"
            adjustment_data["billingGroupId"] = target_id
        else:
            endpoint = "billing/admin/projects/adjustments"
            adjustment_data["projectId"] = target_id

        logger.info(
            "Applying %s adjustment of %s to %s %s for month %s",
            adjustment_type_str,
            adjustment_amount,
            adjustment_target_str,
            target_id,
            self.month,
        )

        try:
            response = self._client.post(endpoint, json_data=adjustment_data)
            logger.info(
                "Successfully applied adjustment to %s %s",
                adjustment_target_str,
                target_id,
            )
        except APIRequestException:
            logger.exception("Failed to apply adjustment")
            raise
        else:
            return response

    def get_adjustments(
        self,
        adjustment_target: AdjustmentTarget | str,
        target_id: str,
        page: int = 1,
        items_per_page: int = 50,
    ) -> list[str]:
        """Get list of adjustment IDs for a target.

        Args:
            adjustment_target: Target type (BillingGroup or Project)
            target_id: ID of the target
            page: Page number for pagination
            items_per_page: Number of items per page

        Returns:
            List of adjustment IDs

        Raises:
            ValidationException: If parameters are invalid
            APIRequestException: If API request fails
        """
        adjustment_target_str = (
            adjustment_target.value
            if isinstance(adjustment_target, AdjustmentTarget)
            else adjustment_target
        )

        # Build endpoint and params
        if adjustment_target_str == AdjustmentTarget.BILLING_GROUP.value:
            endpoint = "billing/admin/billing-groups/adjustments"
            params = {
                "page": page,
                "itemsPerPage": items_per_page,
                "billingGroupId": target_id,
            }
        else:
            endpoint = "billing/admin/projects/adjustments"
            params = {
                "page": page,
                "itemsPerPage": items_per_page,
                "projectId": target_id,
            }

        logger.info(
            "Retrieving adjustments for %s %s", adjustment_target_str, target_id
        )

        try:
            response = self._client.get(endpoint, params=params)
            adjustment_ids = [
                item["adjustmentId"] for item in response.get("adjustments", [])
            ]
            logger.info("Found %d adjustments", len(adjustment_ids))
        except APIRequestException:
            logger.exception("Failed to retrieve adjustments")
            raise
        else:
            return adjustment_ids

    def delete_adjustment(
        self,
        adjustment_ids: str | list[str],
        adjustment_target: AdjustmentTarget | str,
    ) -> None:
        """Delete one or more adjustments.

        Args:
            adjustment_ids: Single adjustment ID or list of IDs to delete
            adjustment_target: Target type (BillingGroup or Project)

        Raises:
            APIRequestException: If any deletion fails
        """
        adjustment_target_str = (
            adjustment_target.value
            if isinstance(adjustment_target, AdjustmentTarget)
            else adjustment_target
        )

        # Normalize to list
        if isinstance(adjustment_ids, str):
            adjustment_ids = [adjustment_ids]

        # Determine endpoint base
        if adjustment_target_str == AdjustmentTarget.BILLING_GROUP.value:
            endpoint_base = "billing/admin/billing-groups/adjustments"
        else:
            endpoint_base = "billing/admin/projects/adjustments"

        # Delete each adjustment
        for adj_id in adjustment_ids:
            logger.info("Deleting adjustment %s", adj_id)

            try:
                self._client.delete(endpoint_base, params={"adjustmentIds": adj_id})
                logger.info("Successfully deleted adjustment %s", adj_id)
            except APIRequestException:
                logger.exception("Failed to delete adjustment %s", adj_id)
                raise

    def delete_all_adjustments(
        self, adjustment_target: AdjustmentTarget | str, target_id: str
    ) -> int:
        """Delete all adjustments for a target.

        Args:
            adjustment_target: Target type (BillingGroup or Project)
            target_id: ID of the target

        Returns:
            Number of adjustments deleted
        """
        adjustment_ids = self.get_adjustments(adjustment_target, target_id)

        if adjustment_ids:
            self.delete_adjustment(adjustment_ids, adjustment_target)

        return len(adjustment_ids)


# Backward compatibility wrapper
class Adjustments:
    """Legacy wrapper for backward compatibility.

    Note: Legacy method names have been deprecated. Please migrate to new names:
    - applyAdjustment() -> apply_adjustment()
    - inquiryAdjustment() -> inquiry_adjustment()
    - deleteAdjustment() -> delete_adjustment()
    """

    def __init__(self, month: str) -> None:
        """Initialize legacy adjustment wrapper."""
        self._manager = AdjustmentManager(month)
        self.month = month

    def apply_adjustment(self, **kwargs: LegacyAdjustmentParams) -> None:
        """Apply adjustment with legacy parameter names.

        Expected kwargs:
            adjustment: Adjustment amount
            adjustmentType: Type of adjustment
            adjustmentTarget: Target type (BillingGroup or Project)
            billingGroupId: Billing group ID (optional)
            projectId: Project ID (optional)
        """
        # Extract parameters with legacy names
        adjustment = kwargs.get("adjustment")
        adjustment_type = kwargs.get("adjustmentType")
        adjustment_target = kwargs.get("adjustmentTarget")
        billing_group_id = kwargs.get("billingGroupId")
        project_id = kwargs.get("projectId")

        # Validate required parameters
        if adjustment is None or adjustment_type is None or adjustment_target is None:
            error_msg = "Missing required parameters: adjustment, adjustmentType, adjustmentTarget"
            raise ValidationException(error_msg)

        target_id = billing_group_id or project_id
        if not target_id:
            error_msg = "Either billingGroupId or projectId must be provided"
            raise ValidationException(error_msg)

        try:
            self._manager.apply_adjustment(
                adjustment_amount=adjustment,
                adjustment_type=adjustment_type,
                adjustment_target=adjustment_target,
                target_id=target_id,
            )
            logger.info("프로젝트 혹은 빌링 그룹의 할인/할증 설정 완료")
        except (APIRequestException, ValidationException):
            logger.exception("할인/할증 등록에 실패하였습니다")

    def inquiry_adjustment(self, **kwargs: LegacyAdjustmentParams) -> list[str] | None:
        """Retrieve adjustments with legacy parameter names.

        Expected kwargs:
            adjustmentTarget: Target type
            billingGroupid: Billing group ID (note lowercase 'id')
            projectId: Project ID

        Returns:
            List of adjustment IDs or None if failed
        """
        adjustment_target = kwargs.get("adjustmentTarget")
        billing_group_id = kwargs.get("billingGroupid")  # Note: lowercase 'id'
        project_id = kwargs.get("projectId")

        # Validate inputs early and return default
        if not adjustment_target:
            logger.error("필수 파라미터 adjustmentTarget이 누락되었습니다")
            return None

        target_id = billing_group_id or project_id
        if not target_id:
            logger.error("billingGroupid 또는 projectId 중 하나가 필요합니다")
            return None

        # Main operation with error handling
        result: list[str] | None = None
        try:
            adjustment_ids = self._manager.get_adjustments(
                adjustment_target=adjustment_target, target_id=target_id
            )
            logger.info(
                "프로젝트 혹은 빌링그룹 AdjustmentId 리스트: %s", adjustment_ids
            )
            result = adjustment_ids
        except (APIRequestException, ValidationException):
            logger.exception("할인/할증 ID 조회에 실패하였습니다")

        return result

    def delete_adjustment(self, adj_id_list: str | list[str]) -> None:
        """Delete adjustments.

        Args:
            adj_id_list: Single adjustment ID or list of IDs to delete
        """
        if not adj_id_list:
            return

        # The original code referenced a global 'adjustmentTarget' which is problematic
        # For backward compatibility, we'll default to Project
        adjustment_target = AdjustmentTarget.PROJECT

        try:
            self._manager.delete_adjustment(adj_id_list, adjustment_target)
            logger.info("프로젝트 혹은 빌링 그룹의 할인/할증 삭제 완료")
        except (APIRequestException, ValidationException):
            logger.exception("할인/할증 삭제에 실패하였습니다")

