# Windows PowerShell script for running billing tests
# Supports Windows 10/11 with PowerShell 5.1+

param(
    [Parameter(Position=0)]
    [string]$TestDir = "tests/unit",
    
    [switch]$Coverage,
    
    [switch]$NoObservability,
    
    [switch]$Verbose,
    
    [string]$Markers = "",
    
    [string]$Pattern = "",
    
    [int]$Parallel = 0,
    
    [switch]$InstallDeps,
    
    [switch]$Docker,
    
    [string]$PytestArgs = "",
    
    [switch]$Help
)

# Show help
if ($Help) {
    Write-Host @"
BillingTest - Windows Test Runner

Usage: .\run_tests_windows.ps1 [options] [test_directory]

Options:
    -TestDir <path>      Test directory to run (default: tests/unit)
    -Coverage            Run with coverage report
    -NoObservability     Exclude observability from coverage
    -Verbose             Verbose output
    -Markers <expr>      Run tests matching mark expression
    -Pattern <pattern>   Run tests matching pattern
    -Parallel <n>        Number of parallel workers
    -InstallDeps         Install dependencies first
    -Docker              Run tests in Docker container
    -PytestArgs <args>   Additional pytest arguments
    -Help                Show this help message

Examples:
    # Run unit tests with coverage
    .\run_tests_windows.ps1 -Coverage
    
    # Run specific tests in parallel
    .\run_tests_windows.ps1 -Pattern "test_payment" -Parallel 4
    
    # Run tests in Docker
    .\run_tests_windows.ps1 -Docker -Coverage
"@
    exit 0
}

# Set error action preference
$ErrorActionPreference = "Stop"

# Get project root
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Function to check if command exists
function Test-Command {
    param($Command)
    
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Find Python command
$PythonCmd = ""
foreach ($cmd in @("python", "python3", "py")) {
    if (Test-Command $cmd) {
        $PythonCmd = $cmd
        break
    }
}

if (-not $PythonCmd) {
    Write-Error "Python not found. Please install Python 3.8+ and add it to PATH."
    exit 1
}

# Show Python version
Write-Host "Using Python: $PythonCmd" -ForegroundColor Green
& $PythonCmd --version

# Install dependencies if requested
if ($InstallDeps) {
    Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
    
    $requirementsFile = Join-Path $ProjectRoot "requirements.txt"
    if (-not (Test-Path $requirementsFile)) {
        Write-Warning "requirements.txt not found"
    } else {
        & $PythonCmd -m pip install -r $requirementsFile
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install dependencies"
            exit 1
        }
        Write-Host "Dependencies installed successfully" -ForegroundColor Green
    }
}

# Run tests in Docker if requested
if ($Docker) {
    Write-Host "`nRunning tests in Docker..." -ForegroundColor Yellow
    
    if (-not (Test-Command "docker")) {
        Write-Error "Docker not found. Please install Docker Desktop for Windows."
        exit 1
    }
    
    # Build Docker command
    $dockerCmd = @(
        "docker", "run", "--rm",
        "-v", "${ProjectRoot}:/app",
        "-w", "/app",
        "python:3.12-slim",
        "bash", "-c"
    )
    
    # Build inner command
    $innerCmd = "pip install -r requirements.txt && python -m pytest"
    
    if ($Coverage) {
        $innerCmd += " --cov=libs --cov-report=term-missing --cov-report=html --cov-report=xml"
        if ($NoObservability) {
            $innerCmd += " --cov-omit=libs/observability/* --cov-omit=libs/dependency_injection.py"
        }
    }
    
    $innerCmd += " $TestDir"
    
    if ($Verbose) { $innerCmd += " -v" } else { $innerCmd += " -q" }
    if ($Markers) { $innerCmd += " -m `"$Markers`"" }
    if ($Pattern) { $innerCmd += " -k `"$Pattern`"" }
    if ($Parallel -gt 0) { $innerCmd += " -n $Parallel" }
    if ($PytestArgs) { $innerCmd += " $PytestArgs" }
    
    $dockerCmd += $innerCmd
    
    & $dockerCmd[0] $dockerCmd[1..($dockerCmd.Length-1)]
    exit $LASTEXITCODE
}

# Build pytest command
$cmd = @($PythonCmd, "-m", "pytest")

# Add coverage options
if ($Coverage) {
    $cmd += "--cov=libs"
    $cmd += "--cov-report=term-missing"
    $cmd += "--cov-report=html"
    $cmd += "--cov-report=xml"
    
    if ($NoObservability) {
        $cmd += "--cov-omit=libs/observability/*"
        $cmd += "--cov-omit=libs/dependency_injection.py"
    }
}

# Add test directory
$cmd += $TestDir

# Add verbosity
if ($Verbose) { $cmd += "-v" } else { $cmd += "-q" }

# Add markers
if ($Markers) {
    $cmd += "-m"
    $cmd += $Markers
}

# Add pattern
if ($Pattern) {
    $cmd += "-k"
    $cmd += $Pattern
}

# Add parallel execution
if ($Parallel -gt 0) {
    $cmd += "-n"
    $cmd += $Parallel
}

# Add additional pytest args
if ($PytestArgs) {
    $cmd += $PytestArgs.Split()
}

# Set environment variables
$env:PYTHONPATH = $ProjectRoot

# Show command if verbose
if ($Verbose) {
    Write-Host "`nRunning command: $($cmd -join ' ')" -ForegroundColor Cyan
    Write-Host "Working directory: $ProjectRoot" -ForegroundColor Cyan
}

# Change to project directory
Push-Location $ProjectRoot

try {
    # Run tests
    Write-Host "`nRunning tests..." -ForegroundColor Yellow
    & $cmd[0] $cmd[1..($cmd.Length-1)]
    
    $exitCode = $LASTEXITCODE
    
    # Show results
    if ($exitCode -eq 0) {
        Write-Host "`nTests passed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`nTests failed with exit code: $exitCode" -ForegroundColor Red
    }
    
    # Show coverage report location if generated
    if ($Coverage) {
        $htmlReport = Join-Path $ProjectRoot "htmlcov" "index.html"
        if (Test-Path $htmlReport) {
            Write-Host "`nCoverage report generated: $htmlReport" -ForegroundColor Cyan
            Write-Host "Open in browser: start $htmlReport" -ForegroundColor Cyan
        }
    }
    
    exit $exitCode
    
} finally {
    Pop-Location
}
