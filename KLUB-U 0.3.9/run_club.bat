@echo off
cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║             КЛУБ-У v1.0                           ║
echo ║  Комплексное Локомотивное Устройство Безопасности ║
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

python -m pip list | find "Pillow" >nul 2>&1
if errorlevel 1 python -m pip install Pillow --break-system-packages --quiet

python -m pip list | find "pyautogui" >nul 2>&1
if errorlevel 1 python -m pip install pyautogui --break-system-packages --quiet

python -m pip list | find "psutil" >nul 2>&1
if errorlevel 1 python -m pip install psutil --break-system-packages --quiet

python -m pip list | find "keyboard" >nul 2>&1
if errorlevel 1 python -m pip install keyboard --break-system-packages --quiet

python main_club.py

pause
