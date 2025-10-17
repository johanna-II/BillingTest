"""In-memory mocked integration tests.

These tests use the `responses` library to mock HTTP requests,
eliminating the need for Docker Mock Server and preventing worker crashes.

Benefits:
- No Docker required
- Ultra-fast execution (< 0.1s per test)
- No worker crashes
- 100% reproducible
"""
