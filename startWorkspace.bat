@echo off
TITLE Flexible Rail Simulator Launcher
SETLOCAL EnableDelayedExpansion

:: 1. SITUARSE EN LA RUTA DEL SCRIPT
cd /d "%~dp0"

echo ============================================
echo      RAIL SIMULATOR - SMART LAUNCHER
echo ============================================

:: --- CONFIGURATION ---
SET PROJECT_DIR=railSim\manage.py
SET VENV_PATH=

echo [1/3] Searching for a virtual environment...

:: 2. BUSCAR AUTOMÁTICAMENTE LA CARPETA DEL ENTORNO
:: Buscamos cualquier carpeta que contenga Scripts\activate.bat
for /d %%i in (*) do (
    if exist "%%i\Scripts\activate.bat" (
        SET VENV_PATH=%%i
        goto :found
    )
)

:found
IF NOT "!VENV_PATH!"=="" (
    echo [2/3] Virtual environment found in: !VENV_PATH!
    echo Activating...
    call "!VENV_PATH!\Scripts\activate"
) ELSE (
    echo [ERROR] No virtual environment found in %CD%
    echo Please create one using: python -m venv name_of_env
    pause
    exit /b
)

:: 3. LANZAR DJANGO
echo [3/3] Starting Django server...
IF EXIST "%PROJECT_DIR%" (
    python "%PROJECT_DIR%" runserver
) ELSE (
    echo [ERROR] Could not find manage.py in %PROJECT_DIR%
    echo Current directory: %CD%
    pause
)

pause