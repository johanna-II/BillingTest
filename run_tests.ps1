# Unified test runner for Windows (PowerShell)
param(
    [ValidateSet("default", "parallel", "safe", "fast", "ultra", "super")]
    [string]$Mode = "default",
    [switch]$NoCoverage,
    [switch]$SkipHealthCheck,
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$PytestArgs
)

Write-Host "Starting tests with mock server (Mode: $Mode)..." -ForegroundColor Green

# Set environment variables
$env:USE_MOCK_SERVER = "true"

# Additional environment variables for optimization modes
if ($Mode -in @("super", "ultra")) {
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
    $env:PYTEST_CURRENT_TEST = "1"
}

# Start mock server in background
Write-Host "Starting mock server..." -ForegroundColor Yellow
$mockProcess = Start-Process python -ArgumentList "-m", "mock_server.run_server" -PassThru -WindowStyle Hidden

# Health check for mock server (unless skipped)
if (-not $SkipHealthCheck) {
    Write-Host "Waiting for mock server to be ready..." -ForegroundColor Yellow
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "Mock server is ready!" -ForegroundColor Green
                $ready = $true
                break
            }
        } catch {
            # Server not ready yet
        }
        Start-Sleep -Seconds 1
    }
    
    if (-not $ready) {
        Write-Host "Mock server failed to start!" -ForegroundColor Red
        Stop-Process -Id $mockProcess.Id -Force -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    # Simple wait when health check is skipped
    Start-Sleep -Seconds 2
}

# Get CPU count for parallel modes
$cpuCount = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
Write-Host "Detected $cpuCount CPU cores" -ForegroundColor Cyan

# Prepare pytest command based on mode
$pytestCmd = @("pytest", "--use-mock")

switch ($Mode) {
    "default" {
        # Basic sequential execution
        $pytestCmd += "-v"
    }
    
    "parallel" {
        # Moderate parallelization
        $workers = [Math]::Max(2, [Math]::Floor($cpuCount / 2))
        Write-Host "Using $workers parallel workers" -ForegroundColor Cyan
        $pytestCmd += "-v", "-n", $workers, "--dist", "loadscope"
    }
    
    "safe" {
        # Run credit tests sequentially first
        Write-Host "Running credit tests sequentially..." -ForegroundColor Cyan
        & pytest --use-mock -v tests/test_credit_all.py tests/test_unpaid_and_credit.py
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Credit tests failed!" -ForegroundColor Red
            Stop-Process -Id $mockProcess.Id -Force
            exit $LASTEXITCODE
        }
        
        # Run remaining tests in parallel
        $workers = [Math]::Max(2, [Math]::Floor($cpuCount / 2))
        Write-Host "Running remaining tests with $workers workers..." -ForegroundColor Cyan
        $pytestCmd += "-v", "-n", $workers, "--dist", "loadscope",
                      "--ignore", "tests/test_credit_all.py",
                      "--ignore", "tests/test_unpaid_and_credit.py"
    }
    
    "fast" {
        # Fast parallel execution without coverage
        $pytestCmd += "-v", "-x", "-n", "auto", "--tb=no", "-q", "--no-cov"
        $NoCoverage = $true
    }
    
    "ultra" {
        # Aggressive parallelization
        $workers = [Math]::Min($cpuCount - 1, 5)
        Write-Host "Using $workers parallel workers" -ForegroundColor Cyan
        $pytestCmd += "-v", "-n", $workers, "--dist", "worksteal",
                      "--maxfail", "5", "--tb=short", "--durations=10",
                      "--no-header", "-p", "no:warnings"
    }
    
    "super" {
        # Maximum optimization
        Write-Host "Running with maximum optimization..." -ForegroundColor Green
        
        # Override pytest settings for speed
        $pytestCmd = @("python", "-m", "pytest", "tests",
                       "--use-mock", "-n", "auto", "--dist", "worksteal",
                       "-x", "--tb=line", "--no-header", "--quiet",
                       "--override-ini=addopts=",
                       "--override-ini=testpaths=tests")
        $NoCoverage = $true
    }
}

# Add coverage flag if needed
if ($NoCoverage -and $Mode -notin @("fast", "super")) {
    $pytestCmd += "--no-cov"
}

# Add user-provided arguments
if ($PytestArgs) {
    $pytestCmd += $PytestArgs
}

# Run tests
Write-Host "Running tests: $($pytestCmd -join ' ')" -ForegroundColor Green
& $pytestCmd[0] $pytestCmd[1..($pytestCmd.Length-1)]

# Store test exit code
$testExitCode = $LASTEXITCODE

# Show summary
if ($testExitCode -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed!" -ForegroundColor Red
}

# Stop mock server
Write-Host "Stopping mock server..." -ForegroundColor Yellow
Stop-Process -Id $mockProcess.Id -Force -ErrorAction SilentlyContinue

# Exit with test exit code
exit $testExitCode
