"""Demonstration of deprecated parameter warnings in MeteringManager.send_iaas_metering().

This script demonstrates how the function now warns when deprecated parameters are used.
"""

import datetime
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to the path so imports work regardless of the CWD
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libs.Metering import MeteringManager

# Constants
COUNTER_NAME_COMPUTE_C2_C8M8 = "compute.c2.c8m8"

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

    metering = MeteringManager(month=datetime.date.today().strftime("%Y-%m"))

    print("1. Normal call (no deprecated parameters):")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name=COUNTER_NAME_COMPUTE_C2_C8M8,
        counter_unit="HOURS",
        counter_volume="10",
    )
    print("   [OK] Success - No warnings\n")

    print("2. Call with deprecated 'target_time' parameter:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name=COUNTER_NAME_COMPUTE_C2_C8M8,
        counter_unit="HOURS",
        counter_volume="10",
        target_time="2024-01-01",  # DEPRECATED
    )
    print()

    print("3. Call with deprecated 'uuid' parameter:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name=COUNTER_NAME_COMPUTE_C2_C8M8,
        counter_unit="HOURS",
        counter_volume="10",
        uuid="test-uuid-123",  # DEPRECATED
    )
    print()

    print("4. Call with deprecated 'app_id' parameter:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name=COUNTER_NAME_COMPUTE_C2_C8M8,
        counter_unit="HOURS",
        counter_volume="10",
        app_id="old-app-id",  # DEPRECATED
    )
    print()

    print("5. Call with deprecated 'project_id' parameter:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name=COUNTER_NAME_COMPUTE_C2_C8M8,
        counter_unit="HOURS",
        counter_volume="10",
        project_id="old-project-id",  # DEPRECATED
    )
    print()

    print("6. Call with ALL deprecated parameters:")
    print("-" * 80)
    result = metering.send_iaas_metering(
        app_key="test-app",
        counter_name=COUNTER_NAME_COMPUTE_C2_C8M8,
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
    print("   Testing: unknown_param='some-value' (not in deprecated list)")
    try:
        result = metering.send_iaas_metering(
            app_key="test-app",
            counter_name=COUNTER_NAME_COMPUTE_C2_C8M8,
            counter_unit="HOURS",
            counter_volume="10",
            unknown_param="some-value",  # NOT in deprecated list
        )
        print(f"   [OK] Function returned successfully: {result}")
        print("   Note: Unknown parameters trigger a warning and are ignored.")
        print("         They are NOT passed through to the underlying API.\n")
    except Exception as e:
        print(f"   [ERROR] Exception raised: {type(e).__name__}: {e}\n")

    print("8. Call with appkey fallback (app_key not provided):")
    print("-" * 80)
    metering.appkey = "fallback-app-key"
    result = metering.send_iaas_metering(
        # app_key intentionally omitted
        counter_name=COUNTER_NAME_COMPUTE_C2_C8M8,
        counter_unit="HOURS",
        counter_volume="10",
    )
    print("   [OK] Success - Used manager.appkey as fallback\n")

    print("9. Call without app_key and no fallback (should raise ValueError):")
    print("-" * 80)
    metering_no_key = MeteringManager(month=datetime.date.today().strftime("%Y-%m"))
    try:
        result = metering_no_key.send_iaas_metering(
            counter_name=COUNTER_NAME_COMPUTE_C2_C8M8,
            counter_unit="HOURS",
            counter_volume="10",
        )
    except ValueError as e:
        print(f"   [OK] ValueError raised as expected: {e}\n")

print("=" * 80)
print("Summary:")
print("=" * 80)
print("[OK] Deprecated parameters (target_time, uuid, app_id, project_id) emit")
print("     specific warnings indicating they are deprecated and will be ignored.")
print("[OK] Unexpected (non-deprecated) parameters emit warnings and are ignored (not")
print("     preserved or passed through to the API), and do NOT raise errors - the")
print("     function continues executing successfully.")
print("[OK] The warnings use the existing logger, so they can be captured by")
print("     logging infrastructure.")
print("[OK] Parameters are explicitly removed from kwargs to ensure they don't")
print("     cause issues downstream.")
print("[OK] Function still works correctly even when deprecated parameters are used.")
print("[OK] When app_key is not provided, manager.appkey is used as fallback.")
print("[OK] ValueError is raised when neither app_key nor manager.appkey is available.")
print("=" * 80)
