@echo off
TITLE Rail Simulator Custom Installer (Poetry Version)
SETLOCAL EnableDelayedExpansion

:: 1. SET SCRIPT DIRECTORY
cd /d "%~dp0"

echo ============================================
echo      RAILSYS - PROJECT CONFIGURATOR
echo ============================================

:: 2. VERIFY PYTHON AVAILABILITY
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python was not detected on this system.
    pause
    exit /b
)

:: 3. VERIFY POETRY INSTALLATION
poetry --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Poetry is not installed or not in the system PATH.
    echo Please install it using: pip install poetry
    pause
    exit /b
)

:: 4. CONFIGURE POETRY (Local Environment)
:: This ensures the .venv folder is created inside the project directory
echo [1/3] Configuring Poetry for local virtual environments...
poetry config virtualenvs.in-project true

:: 5. INSTALL DEPENDENCIES
:: Poetry install will automatically create the .venv if it doesn't exist
if exist "pyproject.toml" (
    echo [2/3] Installing dependencies via Poetry...
    :: Added --no-root to avoid the "package not found" error
    poetry install --no-root
) else (
    echo [ERROR] pyproject.toml file not found.
    echo Make sure you have initialized the project with 'poetry init'.
    pause
    exit /b
)

echo.
echo ============================================
echo      ENVIRONMENT READY (POETRY)
echo ============================================
echo.

:: 6. OPTIONAL SERVER LAUNCH
set /p launch="Do you want to launch the Django server now? (y/n): "
if /i "!launch!"=="y" (
    echo [INFO] Starting server in railSim...
    :: Using 'poetry run' ensures the command runs within the correct virtual environment
    poetry run python railSim\manage.py runserver
) else (
    echo Process finished.
)

pause