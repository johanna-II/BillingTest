@echo off
REM Auto-fix script for Windows
echo.
echo ========================================
echo   Type Check + Lint (Auto-fix)
echo ========================================
echo.

call npm run check:fix

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   All checks passed! ✓
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   Some issues require manual fixing
    echo ========================================
    exit /b 1
)

