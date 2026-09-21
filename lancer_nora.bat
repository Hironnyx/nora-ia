@echo off
title Nora - Mascotte IA de Bureau
chcp 65001 >nul

:: Définition propre du répertoire du projet
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

:: Vérification de l'emplacement du projet
if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    set "PROJECT_DIR=C:\Users\maverick\Documents\Agent ia"
)

cd /d "%PROJECT_DIR%"

echo ===================================================
echo     Demarrage de Nora - Mascotte IA de Bureau
echo ===================================================
echo.
echo Repertoire du projet : "%PROJECT_DIR%"
echo.

set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERREUR CRITIQUE] Impossible de trouver :
    echo "%PYTHON_EXE%"
    echo.
    pause
    exit /b 1
)

echo Nora apparait sur votre bureau...
echo Ne fermez pas cette fenetre pendant l utilisation.
echo.

"%PYTHON_EXE%" desktop_pet.py

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] Nora a rencontre une anomalie.
    pause
)
