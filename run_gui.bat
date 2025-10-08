@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo Starting Game Translator GUI...
echo.
venv310\Scripts\python.exe gui\main_window.py
pause
