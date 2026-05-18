@echo off
chcp 65001 >nul
echo ========================================
echo   SynthResearch - AI Research Platform
echo ========================================
echo.

rem Check Python Environment
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

rem Install Dependencies
echo [1/2] Installing dependencies...
pip install -r requirements.txt -q

rem Start Application
echo [2/2] Starting SynthResearch...
echo.
streamlit run app/main.py --server.port 8502
pause
