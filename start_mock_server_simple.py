"""Simple mock server runner for testing."""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Change to parent directory to ensure proper imports
os.chdir(Path(__file__).parent)

# Import after path setup
from mock_server.app import app

if __name__ == "__main__":
    port = 5000

    # Use Flask development server for simplicity
    app.run(host="0.0.0.0", port=port, debug=False)
