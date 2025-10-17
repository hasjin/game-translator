@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ================================================
echo Game Translator Installation
echo ================================================
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

if not exist "venv310" (
    echo [1/4] Creating virtual environment...
    python -m venv venv310
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)
echo.

echo [2/4] Upgrading pip...
venv310\Scripts\python.exe -m pip install --upgrade pip -q
echo.

echo [3/4] Installing packages...
venv310\Scripts\pip install -q anthropic PyQt6 cryptography pandas openpyxl requests pillow pytesseract matplotlib pyyaml openai googletrans==4.0.0rc1 tqdm
echo [OK] Packages installed
echo.

echo [4/4] Creating directories...
if not exist "config" mkdir config
if not exist "translation_work" mkdir translation_work
if not exist "backups" mkdir backups
if not exist "reports" mkdir reports
echo [OK] Directories created
echo.

echo ================================================
echo Installation Complete!
echo ================================================
echo.
echo Run: run_gui.bat
echo.
pause
