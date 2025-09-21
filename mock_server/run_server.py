"""Standalone script to run the mock server."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mock_server.app import app

if __name__ == "__main__":
    print("Starting Mock Billing API Server with Waitress...")
    print("Server running on http://localhost:5000")
    print("Health check: http://localhost:5000/health")
    
    # Use waitress for production-grade performance
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000, threads=6, cleanup_interval=10, channel_timeout=30)
