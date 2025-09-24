"""Simple mock server runner for testing."""

import sys
from pathlib import Path
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Change to parent directory to ensure proper imports
os.chdir(Path(__file__).parent)

# Import after path setup
from mock_server.app import app

if __name__ == "__main__":
    port = 5000
    print("Starting Mock Billing API Server (Flask development server)...")
    print("Server will be available at:")
    print(f"  - Welcome page: http://localhost:{port}/")
    print(f"  - Swagger UI: http://localhost:{port}/docs")
    print(f"  - Health check: http://localhost:{port}/health")
    print(f"  - API base: http://localhost:{port}/api/v1")
    print("\nPress CTRL+C to stop the server")
    
    # Use Flask development server for simplicity
    app.run(host="0.0.0.0", port=port, debug=False)
