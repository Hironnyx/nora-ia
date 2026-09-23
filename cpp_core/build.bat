@echo off
setlocal
echo =======================================================
echo Compilation de NoraNativeCore (C++20)
echo =======================================================

where cmake >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Configuration CMake...
    if not exist build mkdir build
    cd build
    cmake ..
    cmake --build . --config Release
    cd ..
    echo Compilation terminee avec succes !
    exit /b 0
)

where cl >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Compilation directe via MSVC cl.exe...
    if not exist bin mkdir bin
    cl.exe /std:c++20 /O2 /EHsc /Iinclude src\*.cpp /link gdiplus.lib user32.lib gdi32.lib wininet.lib /OUT:bin\nora_native.exe
    exit /b 0
)

where g++ >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Compilation directe via MinGW g++...
    if not exist bin mkdir bin
    g++ -std=c++20 -O3 -Iinclude src/*.cpp -lgdiplus -luser32 -lgdi32 -lwininet -o bin/nora_native.exe
    exit /b 0
)

echo [Information] Aucun compilateur C++ natif n'est present dans le PATH standard.
echo Les sources C++20 completes et le fichier CMakeLists.txt sont generes et prets pour compilation.
exit /b 0
