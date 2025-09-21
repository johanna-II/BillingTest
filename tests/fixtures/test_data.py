"""
Standard test data fixtures for BillingTest project.

This module provides reusable fixtures for test data setup and teardown.
"""
import pytest
import os
import uuid
from typing import Dict, Any, Optional

from libs import InitializeConfig
from libs import Metering, Credit, Calculation, Contract, Batch
from libs.Payments import Payments


@pytest.fixture
def unique_uuid():
    """Generate a unique UUID for test isolation."""
    return f"TEST_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_config(env, member, month, unique_uuid):
    """
    Standard test configuration with automatic setup and teardown.
    
    This fixture:
    - Creates InitializeConfig with unique UUID
    - Cleans data before test
    - Resets mock server if enabled
    - Automatically cleans up after test
    """
    # Skip for unsupported members
    if member == "etc" and pytest.current_test_name and "credit" in pytest.current_test_name.lower():
        pytest.skip("Credit test should be skipped if member country is not KR or JP")
    
    # Create config with unique UUID
    config = InitializeConfig(env, member, month)
    original_uuid = config.uuid
    config.uuid = f"{original_uuid}_{unique_uuid}"
    
    # Clean data and setup
    config.clean_data()
    config.before_test()
    
    # Reset mock server data if enabled
    if os.environ.get("USE_MOCK_SERVER", "false").lower() == "true":
        _reset_mock_server_data(config.uuid)
    
    yield config
    
    # Cleanup after test
    try:
        config.clean_data()
    except Exception as e:
        print(f"Warning: Cleanup failed: {e}")


@pytest.fixture
def test_metering(test_config, month):
    """Standard Metering object fixture."""
    metering = Metering(month)
    metering.appkey = test_config.appkey[0] if test_config.appkey else "TEST_APPKEY"
    return metering


@pytest.fixture
def test_credit(test_config):
    """Standard Credit object fixture."""
    credit = Credit()
    credit.uuid = test_config.uuid
    credit.campaign_id = test_config.campaign_id
    credit.give_campaign_id = test_config.give_campaign_id
    credit.paid_campaign_id = test_config.paid_campaign_id
    
    yield credit
    
    # Auto-cancel credits after test
    try:
        credit.cancel_credit()
    except Exception as e:
        print(f"Warning: Credit cancellation failed: {e}")


@pytest.fixture
def test_calculation(test_config, month):
    """Standard Calculation object fixture."""
    return Calculation(month, test_config.uuid)


@pytest.fixture
def test_contract(test_config):
    """Standard Contract object fixture."""
    contract = Contract()
    contract.contractIds = test_config.contractIds
    return contract


@pytest.fixture
def test_batch(test_config):
    """Standard Batch object fixture."""
    batch = Batch()
    batch.uuid = test_config.uuid
    return batch


@pytest.fixture
def test_payment(test_config):
    """Standard Payment object fixture."""
    payment = Payments()
    payment.uuid = test_config.uuid
    return payment


@pytest.fixture
def standard_metering_data():
    """Common metering data for tests."""
    return {
        "compute": {
            "counter_name": "compute.c2.c8m8",
            "counter_type": "DELTA",
            "counter_unit": "HOURS",
            "counter_volume": "720"
        },
        "storage": {
            "counter_name": "storage.volume.ssd",
            "counter_type": "DELTA",
            "counter_unit": "KB",
            "counter_volume": "524288000"
        },
        "network": {
            "counter_name": "network.floating_ip",
            "counter_type": "DELTA",
            "counter_unit": "HOURS",
            "counter_volume": "720"
        },
        "gpu": {
            "counter_name": "compute.g2.t4.c8m64",
            "counter_type": "GAUGE",
            "counter_unit": "HOURS",
            "counter_volume": "720"
        }
    }


@pytest.fixture
def standard_credit_amounts():
    """Common credit amounts for tests."""
    return {
        "small": 100000,      # 100,000 KRW
        "medium": 1000000,    # 1,000,000 KRW
        "large": 2000000,     # 2,000,000 KRW
        "event": 50000,       # 50,000 KRW (event credit)
    }


def _reset_mock_server_data(uuid_param: str):
    """Helper function to reset mock server data for a specific UUID."""
    import requests
    
    try:
        response = requests.post(
            "http://localhost:5000/test/reset",
            json={"uuid": uuid_param},
            timeout=1
        )
        if response.status_code == 200:
            print(f"Mock server data reset for UUID: {uuid_param}")
        else:
            print(f"Warning: Mock reset returned {response.status_code}")
    except Exception as e:
        print(f"Warning: Failed to reset mock server data: {e}")


# Composite fixtures for common test scenarios

@pytest.fixture
def billing_test_setup(test_config, test_metering, test_calculation):
    """Complete setup for billing tests."""
    return {
        "config": test_config,
        "metering": test_metering,
        "calculation": test_calculation
    }


@pytest.fixture
def credit_test_setup(test_config, test_metering, test_credit, test_calculation):
    """Complete setup for credit tests."""
    return {
        "config": test_config,
        "metering": test_metering,
        "credit": test_credit,
        "calculation": test_calculation
    }


@pytest.fixture
def contract_test_setup(test_config, test_contract, test_batch):
    """Complete setup for contract tests."""
    return {
        "config": test_config,
        "contract": test_contract,
        "batch": test_batch
    }
