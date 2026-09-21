@echo off
title Nora - Acces Distant 4G / 5G (Tunnel Securise)
chcp 65001 >nul

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

cd /d "%PROJECT_DIR%"

set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"

echo ========================================================
echo       🌸 Nora Mobile - Activation de l'Acces 4G/5G 🌸
echo ========================================================
echo.

"%PYTHON_EXE%" tunnel_manager.py
pause
