@echo off
cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║       ROUTE DIGITIZER - УЛУЧШЕННАЯ ВЕРСИЯ        ║
echo ║    Оцифровка маршрута МТА РЖД (2 направления)    ║
echo ╚════════════════════════════════════════════════════╝
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не установлен
    pause
    exit /b 1
)

python -m pip list | find "PyQt5" >nul 2>&1
if errorlevel 1 python -m pip install PyQt5 --break-system-packages --quiet

echo Запуск Route Digitizer...
echo.

python route_digitizer_improved.py

pause
