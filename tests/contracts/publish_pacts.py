#!/usr/bin/env python3
"""Publish generated pact files to Pact Broker.

This script publishes consumer pact files to a centralized Pact Broker,
enabling provider teams to verify contracts and supporting Can-I-Deploy checks.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("ERROR: requests library required")
    print("Install with: pip install requests")
    sys.exit(1)

from pact_broker_config import (
    PACT_BROKER_URL,
    get_broker_auth,
    get_consumer_version_tags,
    get_publish_version,
    is_broker_configured,
)

PACT_DIR = Path(__file__).parent / "pacts"


def _load_pact_file(pact_file: Path) -> tuple[dict, str, str] | None:
    """Load pact file and extract consumer/provider names.

    Args:
        pact_file: Path to the pact JSON file

    Returns:
        Tuple of (pact_content, consumer, provider) or None if file doesn't exist
    """
    if not pact_file.exists():
        print(f"ERROR: Pact file not found: {pact_file}")
        return None

    with open(pact_file) as f:
        pact_content = json.load(f)

    consumer = pact_content["consumer"]["name"]
    provider = pact_content["provider"]["name"]
    return pact_content, consumer, provider


def _build_auth_headers(auth: tuple | None) -> dict:
    """Build request headers with optional bearer token.

    Args:
        auth: Authentication tuple from get_broker_auth()

    Returns:
        Dictionary of headers
    """
    headers = {"Content-Type": "application/json"}
    if auth and auth[0] == "Bearer":
        headers["Authorization"] = f"Bearer {auth[1]}"
    return headers


def _get_request_auth(auth: tuple | None) -> tuple | None:
    """Get auth parameter for requests library.

    Args:
        auth: Authentication tuple from get_broker_auth()

    Returns:
        Auth tuple for requests or None
    """
    if auth and auth[0] != "Bearer":
        return auth
    return None


def _apply_tags(
    consumer: str,
    consumer_version: str,
    tags: list[str],
    headers: dict,
    auth: tuple | None,
) -> bool:
    """Apply tags to a consumer version.

    Args:
        consumer: Consumer name
        consumer_version: Consumer version string
        tags: List of tags to apply
        headers: Request headers
        auth: Authentication for requests

    Returns:
        True if all tags applied successfully
    """
    request_auth = _get_request_auth(auth)

    for tag in tags:
        encoded_tag = quote(tag, safe="")
        tag_url = (
            f"{PACT_BROKER_URL}/pacticipants/{consumer}/versions/{consumer_version}"
            f"/tags/{encoded_tag}"
        )
        tag_response = requests.put(
            tag_url,
            headers=headers,
            auth=request_auth,
            timeout=10,
        )
        tag_response.raise_for_status()
        print(f"  ✓ Tagged with: {tag}")

    return True


def _set_branch(
    consumer: str,
    consumer_version: str,
    branch: str,
    headers: dict,
    auth: tuple | None,
) -> None:
    """Set branch for a consumer version.

    Args:
        consumer: Consumer name
        consumer_version: Consumer version string
        branch: Branch name
        headers: Request headers
        auth: Authentication for requests
    """
    encoded_branch = quote(branch, safe="")
    branch_url = (
        f"{PACT_BROKER_URL}/pacticipants/{consumer}/branches/{encoded_branch}"
        f"/versions/{consumer_version}"
    )
    request_auth = _get_request_auth(auth)

    try:
        branch_response = requests.put(
            branch_url,
            headers=headers,
            auth=request_auth,
            timeout=10,
        )
        branch_response.raise_for_status()
        print(f"  ✓ Branch set: {branch}")
    except requests.HTTPError:
        print("  ⚠ Branch not supported by broker")


def publish_pact_to_broker(
    pact_file: Path,
    consumer_version: str,
    tags: list[str],
    branch: str = None,
) -> bool:
    """Publish a pact file to the broker.

    Args:
        pact_file: Path to the pact JSON file
        consumer_version: Version of the consumer (e.g., git SHA)
        tags: List of tags to apply (e.g., ['main', 'prod'])
        branch: Branch name for version

    Returns:
        True if successful, False otherwise
    """
    pact_data = _load_pact_file(pact_file)
    if not pact_data:
        return False

    pact_content, consumer, provider = pact_data

    publish_url = (
        f"{PACT_BROKER_URL}/pacts/provider/{provider}/consumer/{consumer}"
        f"/version/{consumer_version}"
    )

    print(f"Publishing pact: {consumer} → {provider}")
    print(f"  Version: {consumer_version}")
    print(f"  Tags: {tags}")
    print(f"  URL: {publish_url}")

    auth = get_broker_auth()
    headers = _build_auth_headers(auth)
    request_auth = _get_request_auth(auth)

    try:
        response = requests.put(
            publish_url,
            json=pact_content,
            headers=headers,
            auth=request_auth,
            timeout=30,
        )
        response.raise_for_status()
        print("  ✓ Published successfully")

        _apply_tags(consumer, consumer_version, tags, headers, auth)

        if branch:
            _set_branch(consumer, consumer_version, branch, headers, auth)

        return True

    except requests.HTTPError as e:
        # 409 Conflict means pact already exists - not a real error
        if e.response.status_code == 409:
            print("  ⚠ Pact already published for this version")
            # Still try to apply tags/branch even if pact exists
            try:
                _apply_tags(consumer, consumer_version, tags, headers, auth)
                if branch:
                    _set_branch(consumer, consumer_version, branch, headers, auth)
                return True
            except requests.RequestException as tag_error:
                print(f"  ✗ Failed to apply tags: {tag_error}")
                return False
        else:
            print(f"  ✗ Failed to publish: {e}")
            return False

    except requests.RequestException as e:
        print(f"  ✗ Failed to publish: {e}")
        return False


def _validate_configuration(dry_run: bool) -> None:
    """Validate broker configuration.

    Args:
        dry_run: Whether this is a dry run

    Raises:
        SystemExit: If configuration is invalid
    """
    if is_broker_configured() or dry_run:
        return

    print("ERROR: Pact Broker not configured")
    print()
    print("Set environment variables:")
    print("  PACT_BROKER_URL=https://your-broker.com")
    print("  PACT_BROKER_TOKEN=your-token")
    print("  OR")
    print("  PACT_BROKER_USERNAME=username")
    print("  PACT_BROKER_PASSWORD=password")
    sys.exit(1)


def _get_pact_files() -> list[Path]:
    """Find all pact files in the pacts directory.

    Returns:
        List of pact file paths

    Raises:
        SystemExit: If no pact files found
    """
    pact_files = list(PACT_DIR.glob("*.json"))
    if not pact_files:
        print("ERROR: No pact files found in {PACT_DIR}")
        sys.exit(1)
    return pact_files


def _publish_pacts(
    pact_files: list[Path],
    version: str,
    tags: list[str],
    branch: str,
    dry_run: bool,
) -> int:
    """Publish all pact files.

    Args:
        pact_files: List of pact files to publish
        version: Consumer version
        tags: Tags to apply
        branch: Branch name
        dry_run: Whether this is a dry run

    Returns:
        Number of successfully published pacts
    """
    success_count = 0
    for pact_file in pact_files:
        if dry_run:
            print(f"Would publish: {pact_file.name}")
            success_count += 1
        else:
            if publish_pact_to_broker(pact_file, version, tags, branch):
                success_count += 1
        print()
    return success_count


def _print_summary(success_count: int, total_count: int) -> int:
    """Print summary and return exit code.

    Args:
        success_count: Number of successful publishes
        total_count: Total number of pacts

    Returns:
        Exit code (0 for success, 1 for partial success)
    """
    print("=" * 70)
    if success_count == total_count:
        print(f"SUCCESS: Published {success_count}/{total_count} pacts")
        return 0
    else:
        print(f"PARTIAL: Published {success_count}/{total_count} pacts")
        return 1


def main():
    """Main entry point for publishing pacts."""
    parser = argparse.ArgumentParser(description="Publish pact files to broker")
    parser.add_argument(
        "--version",
        help="Consumer version (default: from git)",
        default=None,
    )
    parser.add_argument(
        "--tag",
        action="append",
        help="Tag to apply (can be used multiple times)",
        default=None,
    )
    parser.add_argument(
        "--branch",
        help="Branch name",
        default=None,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be published without publishing",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Pact Broker Publisher")
    print("=" * 70)
    print()

    _validate_configuration(args.dry_run)

    # Get version and tags
    version = args.version or get_publish_version()
    tags = args.tag or get_consumer_version_tags()
    branch = args.branch or os.getenv("GIT_BRANCH", "")

    print(f"Broker URL: {PACT_BROKER_URL}")
    print(f"Consumer Version: {version}")
    print(f"Tags: {tags}")
    print(f"Branch: {branch or '(none)'}")
    print()

    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print()

    pact_files = _get_pact_files()
    print(f"Found {len(pact_files)} pact file(s)")
    print()

    success_count = _publish_pacts(pact_files, version, tags, branch, args.dry_run)

    exit_code = _print_summary(success_count, len(pact_files))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
