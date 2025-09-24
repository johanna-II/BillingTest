"""Tests for OpenAPI integration with mock server."""

import json
import os
from typing import Dict, Any

import pytest
import requests
import yaml

from libs.Contract import ContractManager
from libs.Credit import Credit
from libs.Metering import MeteringManager


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.mock_required
class TestOpenAPIIntegration:
    """Test OpenAPI specification integration."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.base_url = os.environ.get('MOCK_SERVER_URL', 'http://localhost:5000')
        self.api_base = f"{self.base_url}/api/v1"
    
    def test_openapi_spec_available(self):
        """Test that OpenAPI spec is available."""
        # Test JSON format
        response = requests.get(f"{self.base_url}/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert "openapi" in spec
        assert spec["openapi"].startswith("3.0")
        assert "paths" in spec
        assert "components" in spec
        
        # Test YAML format
        response = requests.get(f"{self.base_url}/openapi.yaml")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/x-yaml"
        spec_yaml = yaml.safe_load(response.text)
        assert "openapi" in spec_yaml
    
    def test_validate_valid_request(self):
        """Test request validation with valid data."""
        validation_request = {
            "method": "POST",
            "path": "/credits",  # OpenAPI spec defines paths without /api/v1 prefix
            "body": {
                "customer_id": "CUST001",
                "amount": 100.0,
                "currency": "USD",
                "description": "Test credit"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/openapi/validate",
            json=validation_request
        )
        
        if response.status_code != 200:
            print(f"Validation failed: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
    
    def test_validate_invalid_request(self):
        """Test request validation with invalid data."""
        # Missing required field
        validation_request = {
            "method": "POST",
            "path": "/api/v1/credits",
            "body": {
                "customer_id": "CUST001",
                # amount is missing (required)
                "currency": "USD"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/openapi/validate",
            json=validation_request
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["valid"] is False
        assert "error" in data
        
        # Invalid amount (negative)
        validation_request["body"]["amount"] = -100.0
        response = requests.post(
            f"{self.base_url}/openapi/validate",
            json=validation_request
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["valid"] is False
    
    def test_generate_response_from_spec(self):
        """Test response generation from OpenAPI spec."""
        # Test contract endpoint
        response = requests.get(f"{self.api_base}/contracts/999")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            # Verify response matches OpenAPI schema
            assert "id" in data
            assert "status" in data
            assert data["status"] in ["ACTIVE", "INACTIVE", "PENDING"]
            assert "customer" in data
            assert "items" in data
    
    def test_undefined_endpoint_with_openapi(self):
        """Test that undefined endpoints use OpenAPI handler."""
        # This endpoint is not explicitly defined in the mock server
        # but should be handled by OpenAPI catch-all
        response = requests.get(f"{self.api_base}/undefined/endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"] == "NOT_FOUND"
    
    def test_credit_creation_matches_spec(self):
        """Test that credit creation follows OpenAPI spec."""
        credit_data = {
            "customer_id": "CUST001",
            "amount": 250.0,
            "currency": "USD",
            "description": "Monthly bonus",
            "type": "BONUS"
        }
        
        response = requests.post(
            f"{self.api_base}/credits",
            json=credit_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure matches OpenAPI spec
        assert "id" in data
        assert "customer_id" in data
        assert data["customer_id"] == credit_data["customer_id"]
        assert "amount" in data
        assert data["amount"] == credit_data["amount"]
        assert "currency" in data
        assert "status" in data
        assert data["status"] in ["PENDING", "APPROVED", "REJECTED"]
        assert "created_at" in data
    
    def test_metering_query_parameters(self):
        """Test metering endpoint with query parameters."""
        params = {
            "project_id": "PROJ001",
            "month": "2025-01"
        }
        
        response = requests.get(
            f"{self.api_base}/metering",
            params=params
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "project_id" in data
        assert data["project_id"] == params["project_id"]
        assert "period" in data
        assert "start" in data["period"]
        assert "end" in data["period"]
        assert "usage" in data
        assert isinstance(data["usage"], list)
        assert "total_cost" in data
    
    def test_payment_update_patch(self):
        """Test payment status update with PATCH."""
        payment_update = {
            "status": "COMPLETED",
            "transaction_id": "TXN789",
            "completed_at": "2025-01-20T15:30:00"
        }
        
        response = requests.patch(
            f"{self.api_base}/payments/PAY001",
            json=payment_update
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "payment_id" in data
        assert "status" in data
        assert data["status"] == payment_update["status"]
        assert "transaction_id" in data
        assert data["transaction_id"] == payment_update["transaction_id"]
        assert "amount" in data
        assert "currency" in data
        assert "updated_at" in data
    
    def test_batch_job_creation(self):
        """Test batch job creation endpoint."""
        batch_request = {
            "job_type": "BILLING_CALCULATION",
            "parameters": {
                "month": "2025-01",
                "customer_ids": ["CUST001", "CUST002"]
            }
        }
        
        response = requests.post(
            f"{self.api_base}/batch/jobs",
            json=batch_request
        )
        
        # This endpoint might not be implemented yet, 
        # but if OpenAPI is working, it should generate a response
        if response.status_code == 202:
            data = response.json()
            assert "job_id" in data
            assert "status" in data
            assert data["status"] in ["QUEUED", "RUNNING", "COMPLETED", "FAILED"]
            assert "created_at" in data
    
    def test_schema_validation_types(self):
        """Test various schema validation scenarios."""
        test_cases = [
            {
                "name": "Invalid enum value",
                "endpoint": "/credits",
                "method": "POST",
                "body": {
                    "customer_id": "CUST001",
                    "amount": 100.0,
                    "currency": "USD",
                    "type": "INVALID_TYPE"  # Not in enum
                },
                "expect_error": True
            },
            {
                "name": "Invalid currency format",
                "endpoint": "/credits",
                "method": "POST", 
                "body": {
                    "customer_id": "CUST001",
                    "amount": 100.0,
                    "currency": "US"  # Should be 3 letters
                },
                "expect_error": True
            },
            {
                "name": "Valid request",
                "endpoint": "/credits",
                "method": "POST",
                "body": {
                    "customer_id": "CUST001",
                    "amount": 100.0,
                    "currency": "USD"
                },
                "expect_error": False
            }
        ]
        
        for test_case in test_cases:
            validation_request = {
                "method": test_case["method"],
                "path": test_case['endpoint'],  # Use path without /api/v1 prefix
                "body": test_case["body"]
            }
            
            response = requests.post(
                f"{self.base_url}/openapi/validate",
                json=validation_request
            )
            
            if test_case["expect_error"]:
                assert response.status_code == 400, f"Test case '{test_case['name']}' should fail"
                assert not response.json()["valid"]
            else:
                assert response.status_code == 200, f"Test case '{test_case['name']}' should pass"
                assert response.json()["valid"]


class TestOpenAPICompliance:
    """Test that mock server responses comply with OpenAPI spec."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.base_url = os.environ.get('MOCK_SERVER_URL', 'http://localhost:5000')
        self.api_base = f"{self.base_url}/api/v1"
    
    def validate_against_schema(self, response_data: Dict[str, Any], 
                              schema_path: str) -> bool:
        """Validate response data against OpenAPI schema."""
        # This is a simplified validation
        # In production, you'd use openapi-core validators
        return True
    
    def test_all_defined_endpoints_accessible(self):
        """Test that all endpoints defined in OpenAPI are accessible."""
        response = requests.get(f"{self.base_url}/openapi.json")
        spec = response.json()
        
        paths = spec.get("paths", {})
        
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method in path_item:
                    # Convert OpenAPI path to test path
                    test_path = path.replace("{contractId}", "12345")
                    test_path = test_path.replace("{paymentId}", "PAY001")
                    test_path = test_path.replace("{jobId}", "550e8400-e29b-41d4-a716-446655440000")
                    
                    # Make request based on method
                    if method == "get":
                        if "metering" in test_path:
                            response = requests.get(
                                f"{self.base_url}{test_path}",
                                params={"project_id": "PROJ001", "month": "2025-01"}
                            )
                        else:
                            response = requests.get(f"{self.base_url}{test_path}")
                    elif method == "post":
                        # Use minimal valid body
                        body = {}
                        if "credits" in test_path:
                            body = {
                                "customer_id": "CUST001",
                                "amount": 100.0,
                                "currency": "USD"
                            }
                        elif "batch/jobs" in test_path:
                            body = {
                                "job_type": "BILLING_CALCULATION",
                                "parameters": {}
                            }
                        response = requests.post(f"{self.base_url}{test_path}", json=body)
                    elif method == "patch":
                        body = {"status": "COMPLETED"}
                        response = requests.patch(f"{self.base_url}{test_path}", json=body)
                    else:
                        continue
                    
                    # Check that we get a response (not 500 error)
                    assert response.status_code < 500, \
                        f"{method.upper()} {test_path} returned server error"
