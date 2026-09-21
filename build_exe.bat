@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Compilation de Nora en Executable Windows (.exe)

echo ===================================================================
echo   🌸 COMPILATION NORA - EXECUTABLE WINDOWS RAPIDE (.EXE)
echo ===================================================================
echo.
echo Mode : onedir (demarrage instantane ^< 0.5s)
echo Interface : Zero console noire parasite
echo Destination : dist\Nora\Nora.exe
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERREUR] L'environnement virtuel .venv est introuvable.
    pause
    exit /b 1
)

echo [1/2] Lancement du compilateur...
call .venv\Scripts\python.exe build_exe.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERREUR] La compilation a rencontre un probleme.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Compilation terminee avec succes !
echo Le raccourci sur votre Bureau 'Nora' pointe maintenant directement sur Nora.exe.
echo.
pause
