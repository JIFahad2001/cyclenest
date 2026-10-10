@echo off
title CycleNest Console
echo Starting CycleNest Menstrual Tracker...
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo An error occurred. Please ensure Python is installed with dependencies: pip install rich
    pause
)
