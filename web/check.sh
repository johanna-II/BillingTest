#!/bin/bash
# Quick check script for Linux/Mac

echo ""
echo "========================================"
echo "  Type Check + Lint"
echo "========================================"
echo ""

npm run check

if [[ $? -eq 0 ]]; then
    echo ""
    echo "========================================"
    echo "  All checks passed! ✓"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "  Checks failed! Run 'npm run check:fix'"
    echo "========================================"
    exit 1
fi
