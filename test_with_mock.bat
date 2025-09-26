@echo off
echo Setting up mock server environment...
set USE_MOCK_SERVER=true
set MOCK_SERVER_URL=http://localhost:5000

echo Starting mock server in background...
start /B python start_mock_server_simple.py

echo Waiting for mock server to start...
timeout /t 5 /nobreak >nul

echo Running tests with mock server...
pytest %* --use-mock

echo Done!
