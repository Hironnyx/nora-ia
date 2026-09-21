@echo off
title Super-Agent IA Multi-Taches
chcp 65001 >nul

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    set "PROJECT_DIR=C:\Users\maverick\Documents\Agent ia"
)

cd /d "%PROJECT_DIR%"

set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERREUR CRITIQUE] L environnement virtuel .venv n a pas ete trouve dans :
    echo "%PROJECT_DIR%"
    pause
    exit /b 1
)

"%PYTHON_EXE%" main.py
pause
