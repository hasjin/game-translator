@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo Starting Game Translator GUI...
echo.
venv_win\Scripts\python.exe -m gui.main_window
pause
