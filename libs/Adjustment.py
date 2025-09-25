"""Adjustment management for billing system."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypedDict

from config import url

from .constants import DEFAULT_LOCALE, AdjustmentTarget, AdjustmentType
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient

if TYPE_CHECKING:
    from .billing_types import AdjustmentData


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

    def __init__(self, month: str, client: BillingAPIClient | None = None) -> None:
        """Initialize adjustment manager.

        Args:
            month: Target month in YYYY-MM format
            client: Optional BillingAPIClient instance for dependency injection
        """
        self.month = month
        self._client = client if client else BillingAPIClient(url.BASE_BILLING_URL)

    def __repr__(self) -> str:
        """Return string representation of AdjustmentManager."""
        return f"AdjustmentManager(month={self.month})"

    def apply_adjustment(self, **kwargs: Any) -> dict[str, Any]:
        """Apply discount or surcharge to billing group or project.

        Supports both modern and legacy parameter names for backward compatibility.

        Modern parameters:
            adjustment_amount: Amount or percentage of adjustment
            adjustment_type: Type of adjustment (FIXED_DISCOUNT, RATE_DISCOUNT, etc.)
            adjustment_target: Target type (BillingGroup or Project)
            target_id: ID of the target (billing group ID or project ID)
            description: Description of the adjustment

        Legacy parameters:
            adjustment: Amount (legacy name for adjustment_amount)
            adjustmentType: Type (legacy name for adjustment_type)
            adjustmentTarget: Target (legacy name for adjustment_target)
            projectId: Project ID (when target is Project)
            billingGroupId: Billing group ID (when target is BillingGroup)

        Returns:
            API response data

        Raises:
            ValidationException: If parameters are invalid
            APIRequestException: If API request fails
        """
        # Handle both modern and legacy parameter names
        adjustment_amount = kwargs.get("adjustment_amount") or kwargs.get(
            "adjustment", 0
        )
        adjustment_type = kwargs.get("adjustment_type") or kwargs.get("adjustmentType")
        adjustment_target = kwargs.get("adjustment_target") or kwargs.get(
            "adjustmentTarget"
        )
        description = kwargs.get("description", "QA billing automation test")

        # Determine target_id based on target type
        target_id = kwargs.get("target_id")
        if not target_id:
            if adjustment_target in ["Project", "PROJECT"]:
                target_id = kwargs.get("projectId") or kwargs.get("project_id")
            elif adjustment_target in ["BillingGroup", "BILLING_GROUP"]:
                target_id = kwargs.get("billingGroupId") or kwargs.get(
                    "billing_group_id"
                )

        # Validate and normalize parameters
        if adjustment_type is None:
            error_msg = "adjustment_type is required"
            raise ValidationException(error_msg)

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
        adjustment_data: AdjustmentData = {
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
        adjustment_ids: str | list[str] | dict[str, Any],
        adjustment_target: AdjustmentTarget | str | None = None,
    ) -> None:
        """Delete one or more adjustments.

        Args:
            adjustment_ids: Single adjustment ID or list of IDs to delete
            adjustment_target: Target type (BillingGroup or Project)

        Raises:
            APIRequestException: If any deletion fails
        """
        # Handle legacy dict format from inquiry_adjustment
        if isinstance(adjustment_ids, dict):
            actual_adjustments = adjustment_ids.get("adjustments", [])
            if not actual_adjustments:
                logger.info("No adjustments to delete")
                return
            # Extract IDs from adjustment objects
            temp_ids = []
            for adj in actual_adjustments:
                if isinstance(adj, str):
                    # Simple string ID
                    temp_ids.append(adj)
                elif isinstance(adj, dict) and "adjustmentId" in adj:
                    temp_ids.append(adj["adjustmentId"])
                    # Try to infer target if not provided
                    if not adjustment_target:
                        if "billingGroupId" in adj:
                            adjustment_target = AdjustmentTarget.BILLING_GROUP
                        elif "projectId" in adj:
                            adjustment_target = AdjustmentTarget.PROJECT
            adjustment_ids = temp_ids

        if not adjustment_ids:
            logger.info("No adjustment IDs to delete")
            return

        # If target still not determined, raise error
        if not adjustment_target:
            msg = "adjustment_target is required"
            raise ValidationException(msg)

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

    def inquiry_adjustment(
        self,
        billingGroupId: str | None = None,
        projectId: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Legacy method for getting adjustments."""
        if projectId:
            adjustments = self.get_adjustments(AdjustmentTarget.PROJECT, projectId)
            # Return in legacy format
            return {"adjustments": adjustments}
        if billingGroupId:
            adjustments = self.get_adjustments(
                AdjustmentTarget.BILLING_GROUP, billingGroupId
            )
            # Return in legacy format
            return {"adjustments": adjustments}
        # Return empty list if no target specified
        return {"adjustments": []}
