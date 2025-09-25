@echo off
REM Simple test runner wrapper for Windows

REM Default to Docker-based tests
if "%1"=="--local" (
    shift
    python scripts\run_tests.py %* --local
) else (
    python scripts\run_tests.py %*
)
