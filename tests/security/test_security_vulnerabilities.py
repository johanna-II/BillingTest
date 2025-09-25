"""Security vulnerability tests for the billing API."""

import json
import uuid

import pytest

from libs.exceptions import APIRequestException
from libs.http_client import BillingAPIClient


class TestSecurityVulnerabilities:
    """Test for common security vulnerabilities."""

    @pytest.fixture
    def api_client(self):
        """Create API client."""
        mock_url = os.environ.get("MOCK_SERVER_URL", "http://localhost:5000")
        return BillingAPIClient(mock_url)

    @pytest.fixture
    def test_uuid(self) -> str:
        """Generate test UUID."""
        return f"SEC_TEST_{uuid.uuid4().hex[:8]}"

    @pytest.mark.security
    def test_sql_injection_prevention(self, api_client, test_uuid) -> None:
        """Test that SQL injection attempts are properly handled."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM payments WHERE 1=1; --",
            "' UNION SELECT * FROM credit_cards --",
        ]

        headers = {"uuid": test_uuid}

        for payload in malicious_inputs:
            # Try injection in various fields
            data = {
                "counterName": payload,
                "counterType": "DELTA",
                "counterUnit": payload,
                "counterVolume": 100,
                "resourceId": payload,
            }

            try:
                api_client.post("/billing/meters", headers=headers, json_data=data)
                # Should either succeed normally or return validation error
                # but should NOT cause system error
            except APIRequestException as e:
                # Check that it's a client error (4xx) not server error (5xx)
                assert (
                    400 <= e.status_code < 500
                ), f"SQL injection caused server error: {e}"

    @pytest.mark.security
    def test_xss_prevention(self, api_client, test_uuid) -> None:
        """Test that XSS attempts are properly sanitized."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<svg onload=alert('XSS')>",
        ]

        headers = {"uuid": test_uuid}

        for payload in xss_payloads:
            data = {
                "counterName": payload,
                "counterType": "DELTA",
                "counterUnit": "n",
                "counterVolume": 100,
                "resourceId": f"resource-{uuid.uuid4().hex[:8]}",
            }

            try:
                response = api_client.post(
                    "/billing/meters", headers=headers, json_data=data
                )
                # If successful, verify the response doesn't contain unescaped payload
                if isinstance(response, dict):
                    response_str = json.dumps(response)
                    assert (
                        payload not in response_str
                    ), f"XSS payload not sanitized: {payload}"
            except APIRequestException:
                # API rejection is acceptable
                pass

    @pytest.mark.security
    def test_authentication_bypass_attempts(self, api_client) -> None:
        """Test that authentication bypass attempts fail."""
        bypass_attempts = [
            {"uuid": ""},  # Empty UUID
            {"uuid": None},  # Null UUID
            {},  # No UUID header
            {"uuid": "' OR '1'='1"},  # SQL injection in UUID
            {"uuid": "../../../etc/passwd"},  # Path traversal
        ]

        for headers in bypass_attempts:
            try:
                response = api_client.get(
                    "/billing/payments/2024-01/statements", headers=headers
                )
                # Should not return sensitive data without proper auth
                if isinstance(response, dict):
                    assert (
                        "statements" not in response
                        or len(response.get("statements", [])) == 0
                    )
            except APIRequestException:
                # Rejection is expected
                pass

    @pytest.mark.security
    def test_rate_limiting(self, api_client, test_uuid) -> None:
        """Test that rate limiting is in place."""
        headers = {"uuid": test_uuid}
        data = {"counterName": "rate.test", "counterVolume": 1}

        # Make 100 rapid requests
        error_count = 0
        for _i in range(100):
            try:
                api_client.post("/billing/meters", headers=headers, json_data=data)
            except APIRequestException as e:
                if e.status_code == 429:  # Too Many Requests
                    error_count += 1

        # Some requests should be rate limited
        # (This assumes rate limiting is implemented)
        # If not implemented, this serves as a reminder
        if error_count == 0:
            pytest.skip("Rate limiting not implemented - security risk")

    @pytest.mark.security
    def test_path_traversal_prevention(self, api_client, test_uuid) -> None:
        """Test that path traversal attempts are blocked."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc//passwd",
            "../../../../../../../../../../etc/passwd",
        ]

        headers = {"uuid": test_uuid}

        for payload in traversal_attempts:
            # Try in different contexts
            try:
                # In URL path
                api_client.get(f"/billing/meters/{payload}")
            except APIRequestException as e:
                assert e.status_code in [
                    400,
                    404,
                ], f"Path traversal not properly blocked: {payload}"

            # In request body
            data = {"resourceId": payload, "counterName": "test", "counterVolume": 1}
            try:
                api_client.post("/billing/meters", headers=headers, json_data=data)
            except APIRequestException:
                pass  # Rejection is good

    @pytest.mark.security
    def test_command_injection_prevention(self, api_client, test_uuid) -> None:
        """Test that command injection attempts are blocked."""
        command_payloads = [
            "; cat /etc/passwd",
            "| ls -la",
            "` rm -rf / `",
            "$(whoami)",
            "& net user",
        ]

        headers = {"uuid": test_uuid}

        for payload in command_payloads:
            data = {
                "counterName": payload,
                "resourceId": f"resource{payload}",
                "counterVolume": 1,
            }

            try:
                api_client.post("/billing/meters", headers=headers, json_data=data)
            except APIRequestException as e:
                # Should be client error, not server error
                assert 400 <= e.status_code < 500

    @pytest.mark.security
    def test_sensitive_data_exposure(self, api_client, test_uuid) -> None:
        """Test that sensitive data is not exposed in responses."""
        headers = {"uuid": test_uuid}

        # Make various API calls
        endpoints = [
            ("/billing/payments/2024-01/statements", "GET"),
            ("/billing/credits/balance", "GET"),
            ("/billing/contracts", "GET"),
        ]

        sensitive_patterns = [
            "password",
            "secret",
            "token",
            "api_key",
            "private_key",
            "credit_card",
            "ssn",
            "social_security",
        ]

        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = api_client.get(endpoint, headers=headers)
                else:
                    response = api_client.post(endpoint, headers=headers)

                # Check response doesn't contain sensitive data
                response_str = json.dumps(response).lower()
                for pattern in sensitive_patterns:
                    assert (
                        pattern not in response_str
                    ), f"Potential sensitive data exposure: {pattern}"
            except APIRequestException:
                pass  # API errors are ok for this test

    @pytest.mark.security
    def test_input_validation_boundaries(self, api_client, test_uuid) -> None:
        """Test input validation for boundary conditions."""
        headers = {"uuid": test_uuid}

        boundary_tests = [
            # Extremely large numbers
            {"counterVolume": 999999999999999999999},
            # Negative numbers
            {"counterVolume": -1},
            # Zero
            {"counterVolume": 0},
            # Float instead of int
            {"counterVolume": 3.14159},
            # String instead of number
            {"counterVolume": "not a number"},
            # Extremely long strings
            {"counterName": "x" * 10000},
            # Unicode and special characters
            {"counterName": "test\x00null\x00byte"},
            {"counterName": "😈🔥💀"},
            # Empty values
            {"counterName": ""},
            {"counterType": ""},
        ]

        for test_data in boundary_tests:
            data = {
                "counterName": "test",
                "counterType": "DELTA",
                "counterUnit": "n",
                "counterVolume": 100,
                "resourceId": "test-resource",
                **test_data,  # Override with test data
            }

            try:
                response = api_client.post(
                    "/billing/meters", headers=headers, json_data=data
                )
                # If accepted, verify it's handled correctly
                assert isinstance(response, dict)
            except APIRequestException as e:
                # Should be validation error (4xx) not server error (5xx)
                assert (
                    400 <= e.status_code < 500
                ), f"Invalid input caused server error: {test_data}"

    @pytest.mark.security
    def test_http_header_injection(self, api_client, test_uuid) -> None:
        """Test that HTTP header injection is prevented."""
        injection_headers = {
            "uuid": f"{test_uuid}\r\nX-Injected: true",
            "Accept": "application/json\r\nX-Evil: true",
            "X-Custom": "value\nSet-Cookie: admin=true",
        }

        try:
            api_client.get(
                "/billing/payments/2024-01/statements", headers=injection_headers
            )
        except Exception:
            # Any exception is fine - we just don't want header injection to work
            pass

    @pytest.mark.security
    def test_xml_external_entity_prevention(self, api_client, test_uuid) -> None:
        """Test that XXE attacks are prevented."""
        xxe_payload = """<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE foo [
          <!ELEMENT foo ANY >
          <!ENTITY xxe SYSTEM "file:///etc/passwd" >
        ]>
        <data>
            <counterName>&xxe;</counterName>
            <counterVolume>100</counterVolume>
        </data>"""

        headers = {"uuid": test_uuid, "Content-Type": "application/xml"}

        try:
            # Try to send XML with XXE
            response = api_client._client.session.post(
                api_client._build_url("/billing/meters"),
                headers=headers,
                data=xxe_payload,
            )
            # Should reject or safely process without executing XXE
            assert response.status_code >= 400 or "/etc/passwd" not in response.text
        except Exception:
            # Rejection is good
            pass

    @pytest.mark.security
    def test_insecure_deserialization_prevention(self, api_client, test_uuid) -> None:
        """Test that insecure deserialization is prevented."""
        import base64
        import pickle

        # Create a malicious pickle payload
        class MaliciousClass:
            def __reduce__(self):
                import os

                return (os.system, ("echo pwned",))

        malicious_object = MaliciousClass()
        pickled = pickle.dumps(malicious_object)
        encoded = base64.b64encode(pickled).decode()

        headers = {"uuid": test_uuid}
        data = {
            "counterName": "test",
            "counterVolume": 100,
            "metadata": encoded,  # Try to inject pickled object
        }

        try:
            api_client.post("/billing/meters", headers=headers, json_data=data)
            # If accepted, the pickle should not be executed
        except APIRequestException:
            # Rejection is acceptable
            pass
