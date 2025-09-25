#!/bin/bash
# Simple test runner wrapper

# Default to Docker-based tests
if [ "$1" == "--local" ]; then
    shift
    python scripts/run_tests.py "$@" --local
else
    python scripts/run_tests.py "$@"
fi
