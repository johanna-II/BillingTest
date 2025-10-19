"""Compatibility layer for pact-python imports.

This module provides a compatibility layer to handle different versions
of pact-python and potential import issues in CI environments.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Constants
PACT_NOT_INSTALLED_MSG = "pact-python not properly installed"

# Try to import pact components with fallbacks
# Using Pact v3 as primary (stable release)
PACT_AVAILABLE = False

try:
    # Try importing from pact submodules (works for both v2 and v3)
    from pact import Pact, Verifier  # Main classes available in both versions
    from pact.consumer import Consumer, Provider
    from pact.matchers import EachLike, Format, Like, Term

    PACT_AVAILABLE = True
    print(f"✅ Successfully imported pact components (PACT_AVAILABLE={PACT_AVAILABLE})")
    logger.debug("Successfully imported pact components")
except ImportError as e:
    print(f"❌ Failed to import pact components: {e}")
    logger.error(f"Failed to import pact components: {e}")

    try:
        # Last resort: try v3 top-level imports
        from pact import (
            Consumer,
            EachLike,
            Format,
            Like,
            Pact,
            Provider,
            Term,
            Verifier,
        )

        PACT_AVAILABLE = True
        print(
            f"✅ Successfully imported pact v3 components (top-level, PACT_AVAILABLE={PACT_AVAILABLE})"
        )
        logger.debug("Successfully imported pact v3 components (top-level)")
    except ImportError as e2:
        print(f"❌ Failed to import from pact (v3 top-level): {e2}")
        logger.error(f"Failed to import from pact (v3 top-level): {e2}")

        # Create dummy classes for when pact is not available
        class Consumer:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError(PACT_NOT_INSTALLED_MSG)

        class Provider:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError(PACT_NOT_INSTALLED_MSG)

        class Like:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError(PACT_NOT_INSTALLED_MSG)

        class Term:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError(PACT_NOT_INSTALLED_MSG)

        class EachLike:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError(PACT_NOT_INSTALLED_MSG)

        class Format:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError(PACT_NOT_INSTALLED_MSG)

        class Pact:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError(PACT_NOT_INSTALLED_MSG)

        class Verifier:  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError(PACT_NOT_INSTALLED_MSG)

        print(
            f"⚠️ Pact contract testing disabled - all import attempts failed (PACT_AVAILABLE={PACT_AVAILABLE})"
        )
        logger.warning("Pact contract testing disabled - all import attempts failed")

__all__ = [
    "Consumer",
    "Provider",
    "Like",
    "Term",
    "EachLike",
    "Format",
    "Pact",
    "Verifier",
    "PACT_AVAILABLE",
]
