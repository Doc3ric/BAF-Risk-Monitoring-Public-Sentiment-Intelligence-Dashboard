@echo off
REM ========================================================
REM BAF Risk Monitor - Streamlit Web Dashboard Launcher
REM ========================================================
cd /d "%~dp0"

echo [BAF Risk Monitor] Starting Streamlit Intelligence Dashboard...
if exist "venv\Scripts\streamlit.exe" (
    venv\Scripts\streamlit.exe run app.py
) else (
    streamlit run app.py
)
pause
