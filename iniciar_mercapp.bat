@echo off
title MercAPP IS2 - Punto de Venta
cd /d "%~dp0"

echo ========================================================
echo        Iniciando MercAPP IS2 (Punto de Venta)
echo ========================================================
echo.

:: 1. Verificar si existe entorno virtual local
if exist "venv\Scripts\python.exe" (
    echo [INFO] Utilizando entorno virtual local venv...
    "venv\Scripts\python.exe" launcher.py
    goto FIN
)

:: 2. Si no hay venv local, intentar con python global
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Utilizando Python del sistema...
    python launcher.py
    goto FIN
)

echo [ERROR] No se encontro Python ni el entorno virtual.
echo Por favor asegurese de tener Python 3.10 o superior instalado.
pause

:FIN
