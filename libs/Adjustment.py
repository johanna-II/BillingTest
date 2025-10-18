"""Adjustment management for billing system."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypedDict

from config import url

from .adjustment_calculator import AdjustmentCalculator
from .constants import DEFAULT_LOCALE, AdjustmentTarget, AdjustmentType
from .exceptions import APIRequestException, ValidationException
from .http_client import BillingAPIClient

if TYPE_CHECKING:
    from .billing_types import AdjustmentData

# API Endpoints
BILLING_GROUP_ADJUSTMENTS_ENDPOINT = "billing/admin/billing-groups/adjustments"
PROJECT_ADJUSTMENTS_ENDPOINT = "billing/admin/projects/adjustments"


class LegacyAdjustmentParams(TypedDict, total=False):
    """Legacy parameters for adjustment operations."""

    adjustment: float
    adjustmentType: str
    adjustmentTarget: str
    billingGroupId: str
    projectId: str
    billingGroupIdLegacy: str  # Legacy field name for backward compatibility


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

    def _normalize_adjustment_params(
        self, **kwargs: Any
    ) -> tuple[float, str | None, str | None, str, str | None]:
        """Normalize adjustment parameters from both modern and legacy formats.

        Returns:
            Tuple of (adjustment_amount, adjustment_type, adjustment_target, description, target_id)
        """
        # Handle both modern and legacy parameter names
        adjustment_amount = float(
            kwargs.get("adjustment_amount") or kwargs.get("adjustment", 0)
        )
        adjustment_type = kwargs.get("adjustment_type") or kwargs.get("adjustmentType")
        adjustment_target = kwargs.get("adjustment_target") or kwargs.get(
            "adjustmentTarget"
        )
        description = str(kwargs.get("description", "QA billing automation test"))

        # Determine target_id based on target type
        target_id = kwargs.get("target_id")
        if not target_id:
            if adjustment_target in ["Project", "PROJECT"]:
                target_id = kwargs.get("projectId") or kwargs.get("project_id")
            elif adjustment_target in ["BillingGroup", "BILLING_GROUP"]:
                target_id = kwargs.get("billingGroupId") or kwargs.get(
                    "billing_group_id"
                )

        # Convert enum values to strings if needed
        adjustment_type_str = (
            adjustment_type.value
            if isinstance(adjustment_type, AdjustmentType)
            else str(adjustment_type) if adjustment_type else None
        )
        if isinstance(adjustment_target, AdjustmentTarget):
            adjustment_target_str = adjustment_target.value
        elif adjustment_target:
            adjustment_target_str = str(adjustment_target)
        else:
            adjustment_target_str = None

        return (
            adjustment_amount,
            adjustment_type_str,
            adjustment_target_str,
            description,
            target_id,
        )

    def _validate_adjustment_params(
        self,
        adjustment_type: str | None,
        adjustment_target: str | None,
        adjustment_amount: float,
    ) -> None:
        """Validate adjustment parameters.

        Raises:
            ValidationException: If parameters are invalid
        """
        if adjustment_type is None:
            error_msg = "adjustment_type is required"
            raise ValidationException(error_msg)

        if adjustment_target is None:
            error_msg = "adjustment_target is required"
            raise ValidationException(error_msg)

        if adjustment_target not in [t.value for t in AdjustmentTarget]:
            error_msg = f"Invalid adjustment target: {adjustment_target}"
            raise ValidationException(error_msg)

        # Validate amount using AdjustmentCalculator
        AdjustmentCalculator.validate_adjustment_amount(
            adjustment_amount, adjustment_type
        )

    def _build_adjustment_data(
        self, adjustment_amount: float, adjustment_type: str, description: str
    ) -> AdjustmentData:
        """Build the base adjustment data structure."""
        return {
            "adjustment": adjustment_amount,
            "adjustmentTypeCode": adjustment_type,
            "descriptions": [{"locale": DEFAULT_LOCALE, "message": description}],
            "monthFrom": self.month,
            "monthTo": self.month,
            "adjustmentId": None,
            "billingGroupId": None,
            "projectId": None,
        }

    def _get_adjustment_endpoint_and_data(
        self,
        adjustment_target: str,
        target_id: str | None,
        adjustment_data: AdjustmentData,
    ) -> tuple[str, AdjustmentData]:
        """Determine the endpoint and update adjustment data based on target type."""
        if adjustment_target == AdjustmentTarget.BILLING_GROUP.value:
            if target_id is None:
                raise ValidationException(
                    "target_id is required for billing group adjustments"
                )
            endpoint = BILLING_GROUP_ADJUSTMENTS_ENDPOINT
            adjustment_data["billingGroupId"] = target_id
        else:
            if target_id is None:
                raise ValidationException(
                    "target_id is required for project adjustments"
                )
            endpoint = PROJECT_ADJUSTMENTS_ENDPOINT
            adjustment_data["projectId"] = target_id

        return endpoint, adjustment_data

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
        # Normalize parameters
        (
            adjustment_amount,
            adjustment_type,
            adjustment_target,
            description,
            target_id,
        ) = self._normalize_adjustment_params(**kwargs)

        # Validate parameters
        self._validate_adjustment_params(
            adjustment_type, adjustment_target, adjustment_amount
        )

        # After validation, we know these are not None
        assert adjustment_type is not None  # nosec B101
        assert adjustment_target is not None  # nosec B101

        # Build adjustment data
        adjustment_data = self._build_adjustment_data(
            adjustment_amount, adjustment_type, description
        )

        # Get endpoint and update data with target-specific fields
        endpoint, adjustment_data = self._get_adjustment_endpoint_and_data(
            adjustment_target, target_id, adjustment_data
        )

        logger.info(
            "Applying %s adjustment of %s to %s %s for month %s",
            adjustment_type,
            adjustment_amount,
            adjustment_target,
            target_id,
            self.month,
        )

        try:
            response = self._client.post(endpoint, json_data=adjustment_data)
            logger.info(
                "Successfully applied adjustment to %s %s",
                adjustment_target,
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
            endpoint = BILLING_GROUP_ADJUSTMENTS_ENDPOINT
            params = {
                "page": page,
                "itemsPerPage": items_per_page,
                "billingGroupId": target_id,
            }
        else:
            endpoint = PROJECT_ADJUSTMENTS_ENDPOINT
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

    def _extract_adjustment_ids_from_dict(
        self,
        adjustment_dict: dict[str, Any],
        adjustment_target: AdjustmentTarget | str | None,
    ) -> tuple[list[str], AdjustmentTarget | str | None]:
        """Extract adjustment IDs from legacy dict format.

        Returns:
            Tuple of (adjustment_ids, adjustment_target)
        """
        actual_adjustments = adjustment_dict.get("adjustments", [])
        if not actual_adjustments:
            return [], adjustment_target

        temp_ids = []
        for adj in actual_adjustments:
            if isinstance(adj, str):
                temp_ids.append(adj)
            elif isinstance(adj, dict) and "adjustmentId" in adj:
                temp_ids.append(adj["adjustmentId"])
                # Try to infer target if not provided
                if not adjustment_target:
                    adjustment_target = self._infer_adjustment_target(adj)

        return temp_ids, adjustment_target

    def _infer_adjustment_target(
        self, adjustment_dict: dict[str, Any]
    ) -> AdjustmentTarget | None:
        """Infer adjustment target from adjustment dictionary."""
        if "billingGroupId" in adjustment_dict:
            return AdjustmentTarget.BILLING_GROUP
        elif "projectId" in adjustment_dict:
            return AdjustmentTarget.PROJECT
        return None

    def _prepare_adjustment_ids(
        self,
        adjustment_ids: str | list[str] | dict[str, Any],
        adjustment_target: AdjustmentTarget | str | None,
    ) -> tuple[list[str], AdjustmentTarget | str | None]:
        """Prepare adjustment IDs for deletion.

        Returns:
            Tuple of (normalized_ids, adjustment_target)
        """
        if isinstance(adjustment_ids, dict):
            adjustment_ids, adjustment_target = self._extract_adjustment_ids_from_dict(
                adjustment_ids, adjustment_target
            )
        elif isinstance(adjustment_ids, str):
            adjustment_ids = [adjustment_ids]

        return adjustment_ids, adjustment_target

    def _get_delete_endpoint(self, adjustment_target: str) -> str:
        """Get the delete endpoint based on adjustment target."""
        if adjustment_target == AdjustmentTarget.BILLING_GROUP.value:
            return BILLING_GROUP_ADJUSTMENTS_ENDPOINT
        return PROJECT_ADJUSTMENTS_ENDPOINT

    def _delete_single_adjustment(self, endpoint: str, adj_id: str) -> None:
        """Delete a single adjustment."""
        logger.info("Deleting adjustment %s", adj_id)
        try:
            self._client.delete(endpoint, params={"adjustmentIds": adj_id})
            logger.info("Successfully deleted adjustment %s", adj_id)
        except APIRequestException:
            logger.exception("Failed to delete adjustment %s", adj_id)
            raise

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
        # Prepare adjustment IDs
        adjustment_ids, adjustment_target = self._prepare_adjustment_ids(
            adjustment_ids, adjustment_target
        )

        if not adjustment_ids:
            logger.info("No adjustment IDs to delete")
            return

        # Validate target
        if not adjustment_target:
            msg = "adjustment_target is required"
            raise ValidationException(msg)

        # Normalize target to string
        adjustment_target_str = (
            adjustment_target.value
            if isinstance(adjustment_target, AdjustmentTarget)
            else adjustment_target
        )

        # Get endpoint and delete each adjustment
        endpoint = self._get_delete_endpoint(adjustment_target_str)
        for adj_id in adjustment_ids:
            self._delete_single_adjustment(endpoint, adj_id)

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
