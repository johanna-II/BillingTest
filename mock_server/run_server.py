"""Standalone script to run the mock server."""

import os
import signal
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mock_server.app import app


def signal_handler(signum, _frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Get port from environment variable or use default
    port = int(os.environ.get("MOCK_SERVER_PORT", "5000"))

    print(f"Starting mock server on port {port}...")

    # Use waitress for production-grade performance
    from waitress import serve

    serve(
        app,
        host="0.0.0.0",
        port=port,
        threads=6,
        cleanup_interval=10,
        channel_timeout=30,
    )
