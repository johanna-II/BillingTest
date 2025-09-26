#!/bin/bash

echo "Setting up mock server environment..."
export USE_MOCK_SERVER=true
export MOCK_SERVER_URL=http://localhost:5000

echo "Starting mock server in background..."
python start_mock_server_simple.py &
MOCK_PID=$!

echo "Waiting for mock server to start..."
sleep 5

# Check if mock server is running
if curl -s http://localhost:5000/health > /dev/null; then
    echo "Mock server is ready!"
else
    echo "Failed to start mock server"
    exit 1
fi

echo "Running tests with mock server..."
pytest "$@" --use-mock

# Kill mock server
kill $MOCK_PID 2>/dev/null

echo "Done!"
