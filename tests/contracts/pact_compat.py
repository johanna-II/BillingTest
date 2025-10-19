"""Compatibility layer for pact-python v3.

This module provides compatibility wrappers to make pact-python v3
work with v2-style test code.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    # Core classes
    # Import v3 match module (recommended way)
    from pact import Pact, Verifier, match

    _like = match.like
    _regex = match.regex
    _each_like = match.each_like
    _datetime = match.datetime
    _date = match.date

    # Create v2-compatible wrapper classes
    class Like:
        """Wrapper for pact.match.like to match v2 API."""

        def __init__(self, value: Any) -> None:
            self._matcher = _like(value)

        def __repr__(self) -> str:
            return f"Like({self._matcher})"

        def generate(self) -> dict:
            """Generate matcher dict for v3."""
            return self._matcher

    class Term:
        """Wrapper for pact.match.regex to match v2 API."""

        def __init__(self, regex: str, example: str) -> None:
            # v3 API: regex(value, *, regex=pattern)
            # v2 API: Term(pattern, example)
            self._matcher = _regex(example, regex=regex)

        def __repr__(self) -> str:
            return f"Term({self._matcher})"

        def generate(self) -> dict:
            """Generate matcher dict for v3."""
            return self._matcher

    class EachLike:
        """Wrapper for pact.match.each_like to match v2 API."""

        def __init__(self, value: Any, minimum: int = 1) -> None:
            self._matcher = _each_like(value, min=minimum)

        def __repr__(self) -> str:
            return f"EachLike({self._matcher})"

        def generate(self) -> dict:
            """Generate matcher dict for v3."""
            return self._matcher

    class Format:
        """Wrapper for pact.match date/time formatters to match v2 API."""

        @property
        def iso_datetime(self) -> Any:
            """ISO 8601 datetime matcher."""
            return _datetime()

        @property
        def date(self) -> Any:
            """ISO date matcher."""
            return _date()

        def __repr__(self) -> str:
            return "Format()"

    logger.info("Successfully imported pact v3 components")

except ImportError as e:
    logger.error(f"Failed to import pact v3: {e}")
    raise ImportError(
        "pact-python v3 is required for contract testing. "
        "Install with: pip install 'pact-python>=3.1.0'"
    ) from e

__all__ = [
    "Like",
    "Term",
    "EachLike",
    "Format",
    "Pact",
    "Verifier",
]
