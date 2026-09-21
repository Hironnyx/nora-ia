@echo off
title Serveur Nora Mobile (Port 8000)
chcp 65001 >nul

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

cd /d "%PROJECT_DIR%"

set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERREUR] Impossible de trouver l'environnement virtuel .venv
    pause
    exit /b 1
)

echo ========================================================
echo       🌸 Nora Mobile - Serveur de Liaison PC 🌸
echo ========================================================
echo.
echo Adresse locale : http://192.168.1.183:8000
echo Laissez cette fenetre ouverte pour utiliser l'application mobile.
echo.

"%PYTHON_EXE%" -u nora_server.py
pause
