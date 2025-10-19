"""Compatibility layer for pact-python imports.

This module provides a compatibility layer to handle different versions
of pact-python and potential import issues in CI environments.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Try to import pact components with fallbacks
# Using Pact v3 as primary (stable release)
PACT_AVAILABLE = False

try:
    # Try v3 style imports (primary)
    from pact import Consumer, EachLike, Format, Like, Provider, Term

    PACT_AVAILABLE = True
    logger.debug("Successfully imported pact v3 components")
except ImportError as e:
    logger.warning(f"Failed to import from pact (v3 style): {e}")
    logger.info("Attempting v2 fallback imports from pact submodules...")

    try:
        # Fallback to v2 style imports
        from pact.consumer import Consumer, Provider
        from pact.matchers import EachLike, Format, Like, Term

        PACT_AVAILABLE = True
        logger.debug(
            "Successfully imported pact v2 components from submodules (fallback)"
        )
    except ImportError as e2:
        logger.error(f"Failed to import from pact submodules (v2 style): {e2}")

        # Create dummy classes for when pact is not available
        class Consumer:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError("pact-python not properly installed")

        class Provider:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError("pact-python not properly installed")

        class Like:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError("pact-python not properly installed")

        class Term:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError("pact-python not properly installed")

        class EachLike:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError("pact-python not properly installed")

        class Format:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError("pact-python not properly installed")

        # If both import attempts fail, create dummy classes
        if not PACT_AVAILABLE:
            logger.warning(
                "Pact contract testing disabled - all import attempts failed"
            )

__all__ = [
    "Consumer",
    "Provider",
    "Like",
    "Term",
    "EachLike",
    "Format",
    "PACT_AVAILABLE",
]
