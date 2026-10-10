@echo off
title CycleNest Desktop GUI
echo Starting CycleNest Graphical Application...
cd /d "%~dp0"
python gui.py
if errorlevel 1 (
    echo.
    echo An error occurred. Please ensure dependencies are installed:
    echo pip install -r requirements.txt
    pause
)
