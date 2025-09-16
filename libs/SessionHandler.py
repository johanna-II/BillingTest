"""Legacy session handler for backward compatibility.

This module is deprecated. Use http_client.BillingAPIClient instead.
"""

import warnings

from .http_client import SendDataSession as _SendDataSession

warnings.warn(
    "SessionHandler is deprecated. Use libs.http_client.BillingAPIClient instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for backward compatibility
SendDataSession = _SendDataSession
