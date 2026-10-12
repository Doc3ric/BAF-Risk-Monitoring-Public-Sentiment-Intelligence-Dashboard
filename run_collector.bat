@echo off
REM ========================================================
REM BAF Risk Monitor - Standalone Daily Collector Launcher
REM ========================================================
cd /d "%~dp0"

echo [BAF Risk Monitor] Launching Daily Intelligence Collection Pipeline...
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe scripts\collect_daily.py
) else if exist "..\venv\Scripts\python.exe" (
    ..\venv\Scripts\python.exe "%~dp0collect_daily.py"
) else (
    python scripts\collect_daily.py
)

echo [BAF Risk Monitor] Collection Pipeline Completed.
pause
