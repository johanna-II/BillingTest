#!/usr/bin/env python3
"""Debug environment variables and Mock server configuration."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs.Contract import ContractManager
from libs.http_client import BillingAPIClient


def test_environment():
    """Test environment configuration."""
    print("=== Environment Variables ===")
    for key in ["USE_MOCK_SERVER", "MOCK_SERVER_URL", "MOCK_SERVER_PORT"]:
        print(f"{key}: {os.environ.get(key, 'NOT SET')}")

    print("\n=== API Client Configuration ===")

    # Test 1: Default client with base URL
    client1 = BillingAPIClient(base_url="http://localhost:5000/api/v1")
    print(f"Default client base_url: {client1.base_url}")

    # Test 2: Client with explicit URL
    mock_url = os.environ.get("MOCK_SERVER_URL", "http://localhost:5000")
    client2 = BillingAPIClient(base_url=f"{mock_url}/api/v1")
    print(f"Mock client base_url: {client2.base_url}")

    # Test 3: Contract Manager
    print("\n=== Contract Manager Test ===")
    os.environ["USE_MOCK_SERVER"] = "true"
    os.environ["MOCK_SERVER_URL"] = "http://localhost:5000"

    contract_mgr = ContractManager(month="2024-01", billing_group_id="test-bg", client=client2)

    # Check if contract manager has client initialized properly
    if hasattr(contract_mgr, "_client"):
        print("Contract Manager has client initialized")
        client = getattr(contract_mgr, "_client", None)
        if client and hasattr(client, "base_url"):
            print(f"Contract Manager base_url: {client.base_url}")
        else:
            print("Contract Manager client missing base_url")
    else:
        print("Contract Manager has NO CLIENT")

    # Test actual request
    print("\n=== Testing Actual Request ===")
    try:
        # This should fail but show us the URL
        result = contract_mgr.apply_contract(contract_id="test-contract", name="Test Contract")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")


if __name__ == "__main__":
    test_environment()
