"""Vulture whitelist for intentionally unused code.

This file tells vulture to ignore certain patterns that are intentionally unused:
- Abstract method parameters (used by implementations)
- Legacy/deprecated parameters (kept for backward compatibility)
- Context manager __exit__ parameters (protocol requirement)
"""

# ruff: noqa: F821

# Abstract interface parameters (used by implementations)
effective_date
as_of_date
before_date

# Legacy/deprecated parameters (kept for backward compatibility)
target_time
app_id
payments  # verify_assert legacy parameter

# Context manager protocol requirements
exc_type
exc_val
exc_tb
_exc_type
_exc_val
_exc_tb

# Mock/test fixtures
call  # pytest hookimpl parameter
mock_telemetry_cls  # patch decorator
mock_resource  # patch decorator
