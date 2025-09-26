"""Helper utilities for handling flaky tests.

This module provides decorators and utilities to mark and handle
tests that are known to be flaky.
"""

import functools
import time
from collections.abc import Callable
from typing import Any

import pytest


def retry_flaky_test(max_attempts: int = 3, delay: float = 1.0):
    """Decorator to retry flaky tests.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay in seconds between retries
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        print(
                            f"Test {func.__name__} failed (attempt {attempt + 1}/{max_attempts}), retrying..."
                        )
                        time.sleep(delay)
                    else:
                        print(
                            f"Test {func.__name__} failed after {max_attempts} attempts"
                        )

            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


def mark_flaky_in_ci():
    """Mark test as flaky only in CI environment."""
    import os

    if os.environ.get("CI"):
        return pytest.mark.flaky(reruns=3)
    # Don't retry in local development
    return pytest.mark.skip(reason="Flaky test skipped in local development")


def stabilize_test(func: Callable) -> Callable:
    """Decorator to add stabilization techniques to tests.

    This includes:
    - Clearing caches
    - Adding small delays
    - Ensuring clean state
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Clear any caches
        import gc

        gc.collect()

        # Small stabilization delay
        time.sleep(0.1)

        try:
            return func(*args, **kwargs)
        finally:
            # Cleanup
            gc.collect()

    return wrapper


class FlakyTestMonitor:
    """Monitor and report on flaky test behavior."""

    def __init__(self):
        self.test_results = {}

    def record_result(self, test_name: str, passed: bool, duration: float):
        """Record a test result."""
        if test_name not in self.test_results:
            self.test_results[test_name] = {"passes": 0, "failures": 0, "durations": []}

        if passed:
            self.test_results[test_name]["passes"] += 1
        else:
            self.test_results[test_name]["failures"] += 1

        self.test_results[test_name]["durations"].append(duration)

    def get_flakiness_score(self, test_name: str) -> float:
        """Get flakiness score for a test (0-1, higher is more flaky)."""
        if test_name not in self.test_results:
            return 0.0

        results = self.test_results[test_name]
        total = results["passes"] + results["failures"]

        if total == 0:
            return 0.0

        # Calculate flakiness based on failure rate and variance
        failure_rate = results["failures"] / total

        # Add duration variance as a factor
        if len(results["durations"]) > 1:
            avg_duration = sum(results["durations"]) / len(results["durations"])
            variance = sum((d - avg_duration) ** 2 for d in results["durations"]) / len(
                results["durations"]
            )
            normalized_variance = min(
                variance / (avg_duration**2) if avg_duration > 0 else 0, 1.0
            )
        else:
            normalized_variance = 0

        # Combine failure rate and variance
        flakiness = (failure_rate * 0.7) + (normalized_variance * 0.3)

        return min(flakiness, 1.0)


# Example usage in tests:
"""
@pytest.mark.flaky(reruns=3)
def test_potentially_flaky_operation():
    # Test that might fail due to timing issues
    pass

@retry_flaky_test(max_attempts=5, delay=0.5)
def test_with_custom_retry():
    # Test with custom retry logic
    pass

@stabilize_test
def test_needs_stabilization():
    # Test that needs extra stabilization
    pass
"""
