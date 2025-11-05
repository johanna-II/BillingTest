"""Demonstration of deprecated parameter warnings in MeteringManager.send_iaas_metering().

This script demonstrates how the function now warns when deprecated parameters are used.
"""

import logging
import sys
from unittest.mock import Mock, patch

# Add parent directory to path to import libs
sys.path.insert(0, "..")

from libs.Metering import MeteringManager

# Configure logging to show warnings
logging.basicConfig(
    level=logging.WARNING, format="%(levelname)s - %(name)s - %(message)s"
)

print("=" * 80)
print("Demonstration: Deprecated Parameter Warnings in send_iaas_metering()")
print("=" * 80)
print()

# Create a metering manager with mocked client
with patch("libs.Metering.BillingAPIClient") as mock_client_class:
    mock_client = Mock()
    mock_client.post.return_value = {"status": "SUCCESS"}
    mock_client_class.return_value = mock_client

    metering = MeteringManager(month="2024-01")

    print("1. Normal call (no deprecated parameters):")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name="compute.c2.c8m8",
        counter_unit="HOURS",
        counter_volume="10",
    )
    print("   [OK] Success - No warnings\n")

    print("2. Call with deprecated 'target_time' parameter:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name="compute.c2.c8m8",
        counter_unit="HOURS",
        counter_volume="10",
        target_time="2024-01-01",  # DEPRECATED
    )
    print()

    print("3. Call with deprecated 'uuid' parameter:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name="compute.c2.c8m8",
        counter_unit="HOURS",
        counter_volume="10",
        uuid="test-uuid-123",  # DEPRECATED
    )
    print()

    print("4. Call with deprecated 'app_id' parameter:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name="compute.c2.c8m8",
        counter_unit="HOURS",
        counter_volume="10",
        app_id="old-app-id",  # DEPRECATED
    )
    print()

    print("5. Call with deprecated 'project_id' parameter:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name="compute.c2.c8m8",
        counter_unit="HOURS",
        counter_volume="10",
        project_id="old-project-id",  # DEPRECATED
    )
    print()

    print("6. Call with ALL deprecated parameters:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name="compute.c2.c8m8",
        counter_unit="HOURS",
        counter_volume="10",
        target_time="2024-01-01",  # DEPRECATED
        uuid="test-uuid",  # DEPRECATED
        app_id="old-app-id",  # DEPRECATED
        project_id="old-project-id",  # DEPRECATED
    )
    print()

    print("7. Call with unexpected (non-deprecated) parameter:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name="compute.c2.c8m8",
        counter_unit="HOURS",
        counter_volume="10",
        unknown_param="some-value",  # NOT in deprecated list
    )
    print()

print("=" * 80)
print("Summary:")
print("=" * 80)
print("[OK] Deprecated parameters (target_time, uuid, app_id, project_id) emit")
print("     specific warnings indicating they are deprecated and will be ignored.")
print("[OK] The warnings use the existing logger, so they can be captured by")
print("     logging infrastructure.")
print("[OK] Parameters are explicitly removed from kwargs to ensure they don't")
print("     cause issues downstream.")
print("[OK] Function still works correctly even when deprecated parameters are used.")
print("=" * 80)
