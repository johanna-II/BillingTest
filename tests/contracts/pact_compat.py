"""Compatibility layer for pact-python imports.

This module provides a compatibility layer to handle different versions
of pact-python and potential import issues in CI environments.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Try to import pact components with fallbacks
try:
    from pact import Consumer, EachLike, Format, Like, Provider, Term

    PACT_AVAILABLE = True
    logger.debug("Successfully imported pact components (Consumer, Provider API)")
except ImportError as e:
    logger.warning(f"Failed to import Consumer/Provider from pact: {e}")
    logger.info("Attempting fallback imports from pact submodules...")

    try:
        # Try importing from submodules
        from pact.consumer import Consumer, Provider
        from pact.matchers import EachLike, Format, Like, Term

        PACT_AVAILABLE = True
        logger.debug("Successfully imported from pact submodules")
    except ImportError as e2:
        logger.error(f"Failed to import from pact submodules: {e2}")

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

        PACT_AVAILABLE = False
        logger.warning("Pact contract testing disabled - imports failed")

__all__ = [
    "Consumer",
    "Provider",
    "Like",
    "Term",
    "EachLike",
    "Format",
    "PACT_AVAILABLE",
]
