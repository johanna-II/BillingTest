"""Mock server configuration for testing."""

import os

# Mock server settings
USE_MOCK_SERVER = os.environ.get("USE_MOCK_SERVER", "false").lower() == "true"
MOCK_SERVER_HOST = os.environ.get("MOCK_SERVER_HOST", "localhost")
MOCK_SERVER_PORT = int(os.environ.get("MOCK_SERVER_PORT", "5000"))

# Mock server URLs
if USE_MOCK_SERVER:
    # NOSONAR: python:S5332 - HTTP is acceptable for local testing only
    # This configuration is only used for localhost development and CI testing
    # Production environments use HTTPS from url.py
    MOCK_BASE_URL = f"http://{MOCK_SERVER_HOST}:{MOCK_SERVER_PORT}"

    # Override production URLs with mock URLs
    BASE_BILLING_URL = MOCK_BASE_URL
    BASE_METERING_URL = MOCK_BASE_URL
    BASE_CAP_URL = MOCK_BASE_URL
else:
    # Use default production URLs from url.py
    pass
