@echo off
REM Wrapper script to execute log.py via Python interpreter on Windows
REM This wrapper is needed because Windows cannot execute .py files directly
REM %~dp0 is the directory where this batch file is located

REM Try to find Python in the environment
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python "%~dp0log.py" %*
    exit /b %ERRORLEVEL%
)

REM If 'python' not found, try 'python3'
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python3 "%~dp0log.py" %*
    exit /b %ERRORLEVEL%
)

REM If still not found, try 'py' launcher (Windows Python launcher)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py "%~dp0log.py" %*
    exit /b %ERRORLEVEL%
)

REM If all else fails, try direct python.exe in common locations
if exist "C:\Python*\python.exe" (
    for %%i in (C:\Python*\python.exe) do (
        "%%i" "%~dp0log.py" %*
        exit /b %ERRORLEVEL%
    )
)

echo Error: Python interpreter not found. Please ensure Python is installed and in PATH.
exit /b 1
