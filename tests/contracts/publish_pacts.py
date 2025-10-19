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
    if not pact_file.exists():
        print(f"ERROR: Pact file not found: {pact_file}")
        return False

    # Read pact file
    with open(pact_file) as f:
        pact_content = json.load(f)

    consumer = pact_content["consumer"]["name"]
    provider = pact_content["provider"]["name"]

    # Build publish URL
    publish_url = (
        f"{PACT_BROKER_URL}/pacts/provider/{provider}/consumer/{consumer}"
        f"/version/{consumer_version}"
    )

    print(f"Publishing pact: {consumer} → {provider}")
    print(f"  Version: {consumer_version}")
    print(f"  Tags: {tags}")
    print(f"  URL: {publish_url}")

    auth = get_broker_auth()
    headers = {"Content-Type": "application/json"}

    if auth and auth[0] == "Bearer":
        headers["Authorization"] = f"Bearer {auth[1]}"

    try:
        # Publish pact
        response = requests.put(
            publish_url,
            json=pact_content,
            headers=headers,
            auth=auth if auth and auth[0] != "Bearer" else None,
            timeout=30,
        )
        response.raise_for_status()
        print("  ✓ Published successfully")

        # Apply tags
        for tag in tags:
            tag_url = (
                f"{PACT_BROKER_URL}/pacticipants/{consumer}/versions/{consumer_version}"
                f"/tags/{tag}"
            )
            tag_response = requests.put(
                tag_url,
                headers=headers,
                auth=auth if auth and auth[0] != "Bearer" else None,
                timeout=10,
            )
            tag_response.raise_for_status()
            print(f"  ✓ Tagged with: {tag}")

        # Set branch (if supported by broker)
        if branch:
            branch_url = f"{PACT_BROKER_URL}/pacticipants/{consumer}/branches/{branch}/versions/{consumer_version}"
            try:
                branch_response = requests.put(
                    branch_url,
                    headers=headers,
                    auth=auth if auth and auth[0] != "Bearer" else None,
                    timeout=10,
                )
                branch_response.raise_for_status()
                print(f"  ✓ Branch set: {branch}")
            except requests.HTTPError:
                print("  ⚠ Branch not supported by broker")

        return True

    except requests.RequestException as e:
        print(f"  ✗ Failed to publish: {e}")
        return False


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

    # Check configuration
    if not is_broker_configured() and not args.dry_run:
        print("ERROR: Pact Broker not configured")
        print()
        print("Set environment variables:")
        print("  PACT_BROKER_URL=https://your-broker.com")
        print("  PACT_BROKER_TOKEN=your-token")
        print("  OR")
        print("  PACT_BROKER_USERNAME=username")
        print("  PACT_BROKER_PASSWORD=password")
        sys.exit(1)

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

    # Find pact files
    pact_files = list(PACT_DIR.glob("*.json"))
    if not pact_files:
        print("ERROR: No pact files found in {PACT_DIR}")
        sys.exit(1)

    print(f"Found {len(pact_files)} pact file(s)")
    print()

    # Publish each pact
    success_count = 0
    for pact_file in pact_files:
        if args.dry_run:
            print(f"Would publish: {pact_file.name}")
            success_count += 1
        else:
            if publish_pact_to_broker(pact_file, version, tags, branch):
                success_count += 1
        print()

    # Summary
    print("=" * 70)
    if success_count == len(pact_files):
        print(f"SUCCESS: Published {success_count}/{len(pact_files)} pacts")
        sys.exit(0)
    else:
        print(f"PARTIAL: Published {success_count}/{len(pact_files)} pacts")
        sys.exit(1)


if __name__ == "__main__":
    main()
