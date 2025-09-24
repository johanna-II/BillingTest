"""Standalone script to run the mock server."""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mock_server.app import app

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("MOCK_SERVER_PORT", "5000"))

    print("Starting Mock Billing API Server with Waitress...")
    print(f"Server running on http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/health")

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
