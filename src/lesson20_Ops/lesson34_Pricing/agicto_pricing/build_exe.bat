@echo off
REM Build script to create executable from agicto_pricing.py
REM This script:
REM   1. Activates the virtual environment
REM   2. Checks and installs all dependencies from requirements.txt dynamically
REM   3. Installs PyInstaller if needed
REM   4. Uses PyInstaller to package the Flask application

echo ========================================
echo Building Agicto Pricing Executable
echo ========================================
echo.

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Navigate to project root to activate venv
cd /d "%SCRIPT_DIR%..\..\..\.."

REM Activate the virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Error: Virtual environment not found at venv\Scripts\activate.bat
    echo Please ensure you are running this from the correct location.
    pause
    exit /b 1
)

REM Check and install dependencies from requirements.txt
set REQUIREMENTS_FILE=%CD%\requirements.txt

if exist "%REQUIREMENTS_FILE%" (
    echo Checking dependencies from requirements.txt...
    echo File: %REQUIREMENTS_FILE%
    echo.
    
    REM Use pip to check and install missing packages
    REM pip install -r will skip already installed packages and only install missing ones
    echo Installing missing dependencies (this may take a moment)...
    pip install -r "%REQUIREMENTS_FILE%" --quiet --disable-pip-version-check
    if errorlevel 1 (
        echo.
        echo WARNING: Some dependencies may have failed to install.
        echo Continuing anyway - the build may still work if critical packages are installed.
        echo.
    ) else (
        echo Dependencies check completed.
        echo.
    )
) else (
    echo WARNING: requirements.txt not found at: %REQUIREMENTS_FILE%
    echo Skipping dependency check.
    echo.
)

REM Navigate back to the script directory
cd /d "%SCRIPT_DIR%"

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo Building executable...
echo.

REM Create bin directory if it doesn't exist
if not exist "bin" mkdir bin

REM Build the executable
REM --onefile: Create a single executable file
REM --name: Name of the executable
REM --hidden-import: Ensure Flask and other modules are included
REM --console: Keep console window visible to see output/errors
REM --clean: Clean PyInstaller cache before building
REM --icon: Optional icon file (if you have one)
REM --paths: Add src directory to Python path so imports work correctly

pyinstaller --onefile ^
    --name agicto_pricing ^
    --distpath bin ^
    --workpath bin\build ^
    --specpath bin ^
    --console ^
    --paths src ^
    --hidden-import flask ^
    --hidden-import flask.jsonify ^
    --hidden-import flask.render_template_string ^
    --hidden-import requests ^
    --hidden-import bs4 ^
    --hidden-import beautifulsoup4 ^
    --hidden-import agicto_spider ^
    --hidden-import selenium ^
    --hidden-import selenium.webdriver ^
    --hidden-import selenium.webdriver.chrome ^
    --hidden-import selenium.webdriver.chrome.options ^
    --hidden-import selenium.webdriver.chrome.service ^
    --hidden-import selenium.webdriver.common.by ^
    --hidden-import selenium.webdriver.support.ui ^
    --hidden-import selenium.webdriver.support.expected_conditions ^
    --hidden-import selenium.common.exceptions ^
    --hidden-import webdriver_manager ^
    --hidden-import webdriver_manager.chrome ^
    --collect-all flask ^
    --collect-all selenium ^
    --clean ^
    src\agicto_pricing.py

if errorlevel 1 (
    echo.
    echo Build failed! Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo Executable location: bin\agicto_pricing.exe
echo ========================================
echo.
echo To run the application:
echo   Double-click: bin\agicto_pricing.exe
echo   The browser will open automatically.
echo.
echo IMPORTANT NOTES:
echo   - The executable includes Selenium for JavaScript rendering
echo   - ChromeDriver will be automatically downloaded on first run
echo   - Make sure Chrome/Chromium browser is installed on the target machine
echo   - The first run may take longer as ChromeDriver is downloaded
echo.
pause

