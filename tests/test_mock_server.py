"""Test to verify mock server functionality."""

import os
import pytest
import requests

# Only run these tests when mock server is enabled
pytestmark = pytest.mark.skipif(
    os.environ.get("USE_MOCK_SERVER", "false").lower() != "true",
    reason="Mock server tests only run when USE_MOCK_SERVER=true"
)


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.mock_required
class TestMockServer:
    """Test mock server endpoints."""
    
    def setup_method(self):
        """Set up test method with dynamic mock URL."""
        self.mock_url = os.environ.get('MOCK_SERVER_URL', 'http://localhost:5000')
    
    def test_health_check(self):
        """Test mock server health check endpoint."""
        response = requests.get(f"{self.mock_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_metering_creation(self):
        """Test metering data creation."""
        payload = {
            "counterName": "compute.g2.t4.c8m64",
            "counterType": "GAUGE",
            "counterUnit": "HOURS",
            "counterVolume": "720"
        }
        
        response = requests.post(f"{self.mock_url}/billing/meters", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["header"]["isSuccessful"] is True
        assert "meterId" in data
    
    def test_credit_history(self):
        """Test credit history retrieval."""
        response = requests.get(f"{self.mock_url}/billing/credits/history?uuid=test-user")
        assert response.status_code == 200
        data = response.json()
        assert data["header"]["isSuccessful"] is True
        assert "totalCreditAmt" in data
    
    def test_billing_detail(self):
        """Test billing detail retrieval."""
        response = requests.get(f"{self.mock_url}/billing/v5.0/bills/detail?uuid=test-user&month=2024-01")
        assert response.status_code == 200
        data = response.json()
        assert data["header"]["isSuccessful"] is True
        assert "totalAmount" in data
        assert "charge" in data
        assert "vat" in data
        assert "statements" in data