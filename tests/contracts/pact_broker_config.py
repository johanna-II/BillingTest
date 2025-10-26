"""Pact Broker configuration for contract publishing and verification.

This module provides configuration for Pact Broker integration,
enabling centralized contract management and Can-I-Deploy checks.
"""

import os
from typing import Optional

# Pact Broker Configuration
PACT_BROKER_URL = os.getenv("PACT_BROKER_URL", "https://pact-broker.example.com")
PACT_BROKER_USERNAME = os.getenv("PACT_BROKER_USERNAME", "")
PACT_BROKER_PASSWORD = os.getenv("PACT_BROKER_PASSWORD", "")
PACT_BROKER_TOKEN = os.getenv("PACT_BROKER_TOKEN", "")

# Application versioning
APP_VERSION = os.getenv("GIT_COMMIT", os.getenv("CI_COMMIT_SHA", "dev"))
APP_BRANCH = os.getenv("GIT_BRANCH", os.getenv("CI_COMMIT_BRANCH", "local"))

# Consumer/Provider names
CONSUMER_NAME = "BillingTest"
PROVIDER_NAME = "BillingAPI"


def get_broker_auth() -> Optional[tuple[str, str]]:
    """Get Pact Broker authentication credentials.

    Returns:
        Tuple of (username, password) if configured, None otherwise
    """
    if PACT_BROKER_TOKEN:
        return ("Bearer", PACT_BROKER_TOKEN)
    elif PACT_BROKER_USERNAME and PACT_BROKER_PASSWORD:
        return (PACT_BROKER_USERNAME, PACT_BROKER_PASSWORD)
    return None


def is_broker_configured() -> bool:
    """Check if Pact Broker is configured.

    Returns:
        True if broker URL and auth are configured
    """
    return bool(PACT_BROKER_URL) and bool(get_broker_auth())


def get_publish_version() -> str:
    """Get version to use when publishing pacts.

    Returns:
        Git commit SHA or 'dev' for local development
    """
    return APP_VERSION


def get_consumer_version_tags() -> list[str]:
    """Get tags to apply to published consumer version.

    Returns:
        List of tags (e.g., ['main', 'prod'])
    """
    tags = []

    # Add branch tag
    if APP_BRANCH:
        tags.append(APP_BRANCH)

    # Add environment tags
    if APP_BRANCH == "main":
        tags.append("prod")
    elif APP_BRANCH in ["develop", "development"]:
        tags.append("dev")

    return tags


__all__ = [
    "PACT_BROKER_URL",
    "CONSUMER_NAME",
    "PROVIDER_NAME",
    "get_broker_auth",
    "is_broker_configured",
    "get_publish_version",
    "get_consumer_version_tags",
]
