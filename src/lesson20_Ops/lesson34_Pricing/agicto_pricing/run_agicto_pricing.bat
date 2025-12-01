@echo off
REM Batch file to run agicto_pricing.py
REM This script:
REM   1. Activates the virtual environment
REM   2. Checks and installs all dependencies from requirements.txt dynamically
REM   3. Runs the Flask web interface

REM Keep window open on error
setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "LOG_FILE=%SCRIPT_DIR%run_agicto_pricing.log"

REM Redirect all output to log file AND console
call :log "========================================"
call :log "Starting Agicto Pricing Web Interface"
call :log "========================================"
call :log "Log file: %LOG_FILE%"
call :log ""

REM Function to log and display
goto :main

:log
if not "%~1"=="" (
    echo %~1
    echo [%date% %time%] %~1 >> "%LOG_FILE%"
) else (
    echo.
    echo. >> "%LOG_FILE%"
)
exit /b

:main

REM Navigate to the project root (4 levels up from agicto_pricing folder)
cd /d "%SCRIPT_DIR%..\..\..\.."
if errorlevel 1 (
    call :log "ERROR: Failed to navigate to project root"
    call :log "Current directory: %CD%"
    call :log "Script directory: %SCRIPT_DIR%"
    pause
    exit /b 1
)

call :log "Project root: %CD%"
call :log ""

REM Activate the virtual environment
if exist "venv\Scripts\activate.bat" (
    call :log "Activating virtual environment..."
    call venv\Scripts\activate.bat >nul 2>&1
    if errorlevel 1 (
        call :log "ERROR: Failed to activate virtual environment"
        pause
        exit /b 1
    )
    call :log "Virtual environment activated."
) else (
    call :log "ERROR: Virtual environment not found at venv\Scripts\activate.bat"
    call :log "Current directory: %CD%"
    call :log "Please ensure you are running this from the correct location."
    pause
    exit /b 1
)

REM Check and install dependencies from requirements.txt
set "REQUIREMENTS_FILE=%CD%\requirements.txt"

if exist "%REQUIREMENTS_FILE%" (
    call :log "Checking dependencies from requirements.txt..."
    call :log "File: %REQUIREMENTS_FILE%"
    call :log ""
    
    REM Use pip to check and install missing packages
    REM pip install -r will skip already installed packages and only install missing ones
    call :log "Installing missing dependencies (this may take a moment)..."
    pip install -r "%REQUIREMENTS_FILE%" --quiet --disable-pip-version-check >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        call :log ""
        call :log "WARNING: Some dependencies may have failed to install."
        call :log "Continuing anyway - the app may still work if critical packages are installed."
        call :log ""
    ) else (
        call :log "Dependencies check completed."
        call :log ""
    )
) else (
    call :log "WARNING: requirements.txt not found at: %REQUIREMENTS_FILE%"
    call :log "Skipping dependency check."
    call :log ""
    
    REM Fallback: Check for critical packages individually
    call :log "Checking critical packages..."
    python -c "import flask" 2>nul
    if errorlevel 1 (
        call :log "Installing Flask..."
        pip install flask >> "%LOG_FILE%" 2>&1
    )
    
    python -c "import selenium" 2>nul
    if errorlevel 1 (
        call :log "Installing Selenium..."
        pip install selenium webdriver-manager >> "%LOG_FILE%" 2>&1
    )
    
    python -c "import bs4" 2>nul
    if errorlevel 1 (
        call :log "Installing BeautifulSoup4..."
        pip install beautifulsoup4 >> "%LOG_FILE%" 2>&1
    )
    
    python -c "import requests" 2>nul
    if errorlevel 1 (
        call :log "Installing Requests..."
        pip install requests >> "%LOG_FILE%" 2>&1
    )
    call :log ""
)

REM Navigate back to the script directory
cd /d "%SCRIPT_DIR%"
if errorlevel 1 (
    call :log "ERROR: Failed to navigate to script directory: %SCRIPT_DIR%"
    pause
    exit /b 1
)

REM Verify the Python script exists
if not exist "%SCRIPT_DIR%src\agicto_pricing.py" (
    call :log "ERROR: Python script not found at: %SCRIPT_DIR%src\agicto_pricing.py"
    call :log "Current directory: %CD%"
    pause
    exit /b 1
)

REM Run the Python script in a new window with --no-browser flag
REM This prevents the Python script from opening the browser automatically
REM The batch file will control when to open the browser instead
REM IMPORTANT: The new window needs to activate venv too!
REM Change to src directory to run the script (so imports work correctly)
call :log ""
call :log "Starting Flask server..."
call :log "Script location: %SCRIPT_DIR%src\agicto_pricing.py"
call :log ""

REM Build paths properly - resolve relative paths first
cd /d "%SCRIPT_DIR%..\..\..\.."
set "PROJECT_ROOT=%CD%"
cd /d "%SCRIPT_DIR%src"
set "SRC_DIR=%CD%"
cd /d "%SCRIPT_DIR%"

REM Create a temporary batch file to run the server (avoids quote/path issues)
set "TEMP_BAT=%TEMP%\agicto_server_%RANDOM%.bat"
(
    echo @echo off
    echo cd /d "%PROJECT_ROOT%"
    echo call venv\Scripts\activate.bat
    echo cd /d "%SRC_DIR%"
    echo python agicto_pricing.py --no-browser
    echo pause
) > "%TEMP_BAT%"

call :log "Temporary server script created: %TEMP_BAT%"
start "Agicto Pricing Server" cmd /k ""%TEMP_BAT%""

if errorlevel 1 (
    call :log "ERROR: Failed to start Flask server"
    pause
    exit /b 1
)

REM Wait a moment for the server to start
call :log "Waiting for server to start..."
timeout /t 5 /nobreak >nul

REM Open the URL in the default browser
REM This is controlled by the batch file, not the Python script
call :log "Opening http://localhost:5000 in your default browser..."
start http://localhost:5000

call :log ""
call :log "========================================"
call :log "Server is running!"
call :log "========================================"
call :log ""
call :log "- Flask server is running in the 'Agicto Pricing Server' window"
call :log "- Close that window to stop the application"
call :log "- If the browser didn't open, manually visit: http://localhost:5000"
call :log "- Check log file for details: %LOG_FILE%"
call :log ""
call :log "Script completed successfully."
echo.
echo ========================================
echo Server is running!
echo ========================================
echo.
echo - Flask server is running in the "Agicto Pricing Server" window
echo - Close that window to stop the application
echo - If the browser didn't open, manually visit: http://localhost:5000
echo - Check log file for details: %LOG_FILE%
echo.
pause

