@echo off
TITLE Rail Simulator Custom Installer
SETLOCAL EnableDelayedExpansion

:: 1. SITUARSE EN EL DIRECTORIO DEL SCRIPT
cd /d "%~dp0"

echo ============================================
echo      RAIL SIMULATOR - CONFIGURADOR
echo ============================================

:: 2. PREGUNTAR POR EL NOMBRE DEL ENTORNO
echo.
set /p VENV_NAME="Introduce el nombre para tu entorno virtual (Presiona Enter para usar 'venv_tfg'): "

:: Si el usuario deja el nombre vacio, asignamos uno por defecto
if "!VENV_NAME!"=="" set VENV_NAME=venv_tfg

echo [INFO] Se usara el nombre: !VENV_NAME!
echo.

:: 3. VERIFICAR SI PYTHON ESTA DISPONIBLE
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] No se detecto Python en el sistema.
    pause
    exit /b
)

:: 4. CREACION O ACTIVACION
if not exist "!VENV_NAME!\" (
    echo [1/3] Creando entorno virtual: !VENV_NAME!...
    python -m venv !VENV_NAME!
) else (
    echo [1/3] El entorno '!VENV_NAME!' ya existe.
)

:: 5. ACTIVACION
echo [2/3] Activando entorno...
call "!VENV_NAME!\Scripts\activate"

:: 6. INSTALACION DE LIBRERIAS
:: Esto asegura que pymongo, matplotlib y geopy esten listos
if exist "requirements.txt" (
    echo [3/3] Instalando dependencias desde requirements.txt...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo [SKIP] No se encontro requirements.txt.
)

echo.
echo ============================================
echo    ENTORNO !VENV_NAME! LISTO
echo ============================================
echo.

:: 7. LANZAMIENTO OPCIONAL
set /p launch="¿Quieres lanzar el servidor de Django ahora? (s/n): "
if /i "!launch!"=="s" (
    echo [INFO] Iniciando servidor en railSim...
    :: Esto ejecuta manage.py usando la configuracion de simLibrary
    python railSim\manage.py runserver
) else (
    echo Proceso finalizado.
)

pause