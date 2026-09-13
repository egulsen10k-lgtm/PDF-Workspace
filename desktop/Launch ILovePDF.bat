@echo off
TITLE ILovePDF Personal Local Edition - Launcher
color 0A
cls

echo ================================================================
echo   ILovePDF Personal Local Edition - Windows Desktop Pack
echo ================================================================
echo.

:: 1. Check for Python 3
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 is not installed or not added to PATH.
    echo Please download and install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

:: 2. Check for Node.js (npm)
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not added to PATH.
    echo Please download and install Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking Python environment and dependencies...
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\python -m pip install --upgrade pip
    call venv\Scripts\pip install -r backend\requirements.txt
    call venv\Scripts\pip install pywebview
)

echo [2/4] Checking Frontend dependencies and build...
if not exist frontend\node_modules (
    echo Installing Node.js dependencies (this may take a minute)...
    cd frontend
    call npm install
    cd ..
)

if not exist frontend\.next (
    echo Building Next.js production frontend...
    cd frontend
    call npm run build
    cd ..
)

echo [3/4] Ensuring data and storage folders exist...
if not exist data\storage (
    mkdir data\storage
    mkdir data\storage\originals
    mkdir data\storage\outputs
    mkdir data\storage\previews
    mkdir data\storage\backups
)

echo [4/4] Launching ILovePDF Personal Desktop App...
echo.
echo ================================================================
echo   The app window will open shortly.
echo   To shut down, simply close the app window.
echo ================================================================

call venv\Scripts\python desktop\launcher.py
pause
