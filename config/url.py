# Check if mock mode is enabled
import os

USE_MOCK_SERVER = os.environ.get("USE_MOCK_SERVER", "false").lower() == "true"

if USE_MOCK_SERVER:
    # Use mock server URLs
    BASE_BILLING_URL = "http://localhost:5000"
    BASE_METERING_URL = "http://localhost:5000"
    BASE_CAP_URL = "http://localhost:5000"
else:
    # Default production URLs
    BASE_BILLING_URL = "https://billingtest.internal.com"
    BASE_METERING_URL = "https://meteringtest.internal.com"
    BASE_CAP_URL = "https://cabtest.internal.com"

METERING_URL = f"{BASE_METERING_URL}/billing/meters"
METERING_ADMIN_URL = f"{BASE_METERING_URL}/billing/admin"
BILLING_ADMIN_URL = f"{BASE_BILLING_URL}/billing/admin"
BILLING_CONSOLE_URL = f"{BASE_BILLING_URL}/billing/"
BILLING_CONSOLE_V5 = f"{BASE_BILLING_URL}/billing/v5.0"
BILLING_QA_URL = f"{BASE_BILLING_URL}/billing/qa"
ALPHA_CAB_URL = f"{BASE_CAP_URL}/api/projects/"
CREDIT_COUPON_URL = f"{BASE_BILLING_URL}/billing/coupons/"
CREDIT_GIVE_URL = f"{BASE_BILLING_URL}/billing/admin/campaign/"
CREDIT_HISTORY_URL = f"{BASE_BILLING_URL}/billing/credits/history"

# Export all public constants
__all__ = [
    "ALPHA_CAB_URL",
    "BASE_BILLING_URL",
    "BASE_CAP_URL",
    "BASE_METERING_URL",
    "BILLING_ADMIN_URL",
    "BILLING_CONSOLE_URL",
    "BILLING_CONSOLE_V5",
    "BILLING_QA_URL",
    "CREDIT_COUPON_URL",
    "CREDIT_GIVE_URL",
    "CREDIT_HISTORY_URL",
    "METERING_ADMIN_URL",
    "METERING_URL",
]
