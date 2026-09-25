@echo off
title Nora Station Launcher
cd /d "%~dp0"
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0desktop_pet.py"
exit
