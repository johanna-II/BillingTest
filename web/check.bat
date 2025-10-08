@echo off
REM Quick check script for Windows
echo.
echo ========================================
echo   Type Check + Lint
echo ========================================
echo.

call npm run check

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   All checks passed! ✓
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   Checks failed! Run 'npm run check:fix'
    echo ========================================
    exit /b 1
)

