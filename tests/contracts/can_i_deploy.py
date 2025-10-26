#!/usr/bin/env python3
"""Check if it's safe to deploy using Pact Can-I-Deploy.

This script queries the Pact Broker to verify all consumer-provider
contracts are compatible before deployment.
"""

import argparse
import sys

try:
    import requests
except ImportError:
    print("ERROR: requests library required")
    print("Install with: pip install requests")
    sys.exit(1)

from pact_broker_config import (
    CONSUMER_NAME,
    PACT_BROKER_URL,
    get_broker_auth,
    get_publish_version,
    is_broker_configured,
)


def can_i_deploy(
    pacticipant: str,
    version: str,
    to_environment: str = None,
) -> tuple[bool, str]:
    """Check if a version can be deployed.

    Args:
        pacticipant: Name of consumer or provider
        version: Version to check
        to_environment: Target environment (e.g., 'production')

    Returns:
        Tuple of (can_deploy: bool, message: str)
    """
    # Build can-i-deploy URL
    url = f"{PACT_BROKER_URL}/matrix"

    params = {
        "q[][pacticipant]": pacticipant,
        "q[][version]": version,
        "latestby": "cvp",
    }

    if to_environment:
        params["environment"] = to_environment

    print(f"Checking deployment safety for {pacticipant} v{version}")
    if to_environment:
        print(f"  Target environment: {to_environment}")
    print(f"  URL: {url}")
    print()

    auth = get_broker_auth()
    headers = {}

    if auth and auth[0] == "Bearer":
        headers["Authorization"] = f"Bearer {auth[1]}"

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            auth=auth if auth and auth[0] != "Bearer" else None,
            timeout=30,
        )
        response.raise_for_status()

        matrix = response.json()

        # Check verification results
        summary = matrix.get("summary", {})
        deployable = summary.get("deployable", False)
        reason = summary.get("reason", "Unknown")

        # Print results
        print("=" * 70)
        if deployable:
            print("✓ SAFE TO DEPLOY")
        else:
            print("✗ NOT SAFE TO DEPLOY")
        print("=" * 70)
        print()
        print(f"Reason: {reason}")
        print()

        # Print verification matrix
        if "matrix" in matrix:
            print("Verification Matrix:")
            for entry in matrix["matrix"]:
                consumer = entry.get("consumer", {})
                provider = entry.get("provider", {})
                verification = entry.get("verificationResult", {})

                consumer_name = consumer.get("name", "Unknown")
                consumer_version = consumer.get("version", {}).get("number", "Unknown")
                provider_name = provider.get("name", "Unknown")
                verified = verification.get("success", False)

                status = "✓" if verified else "✗"
                print(
                    f"  {status} {consumer_name} v{consumer_version} → {provider_name}"
                )

        return deployable, reason

    except requests.RequestException as e:
        return False, f"Broker request failed: {e}"


def main():
    """Main entry point for can-i-deploy check."""
    parser = argparse.ArgumentParser(
        description="Check if it's safe to deploy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check if consumer can be deployed
  python can_i_deploy.py --pacticipant BillingTest --version abc123

  # Check deployment to production
  python can_i_deploy.py --pacticipant BillingTest --version abc123 --to production

  # Dry run (show what would be checked)
  python can_i_deploy.py --dry-run
        """,
    )
    parser.add_argument(
        "--pacticipant",
        help="Consumer or provider name",
        default=CONSUMER_NAME,
    )
    parser.add_argument(
        "--version",
        help="Version to check (default: current git commit)",
        default=None,
    )
    parser.add_argument(
        "--to",
        dest="to_environment",
        help="Target environment (e.g., production, staging)",
        default=None,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show configuration without making requests",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Pact Can-I-Deploy Check")
    print("=" * 70)
    print()

    # Check configuration
    if not is_broker_configured() and not args.dry_run:
        print("ERROR: Pact Broker not configured")
        print()
        print("Set environment variables:")
        print("  PACT_BROKER_URL=https://your-broker.com")
        print("  PACT_BROKER_TOKEN=your-token")
        sys.exit(1)

    version = args.version or get_publish_version()

    if args.dry_run:
        print("DRY RUN MODE")
        print(f"Would check: {args.pacticipant} v{version}")
        if args.to_environment:
            print(f"Target: {args.to_environment}")
        sys.exit(0)

    # Perform can-i-deploy check
    can_deploy, _ = can_i_deploy(
        args.pacticipant,
        version,
        args.to_environment,
    )

    if can_deploy:
        print()
        print("=" * 70)
        print("RESULT: Safe to deploy ✓")
        print("=" * 70)
        sys.exit(0)
    else:
        print()
        print("=" * 70)
        print("RESULT: NOT safe to deploy ✗")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
