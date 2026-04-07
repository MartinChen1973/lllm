@echo off

setlocal EnableExtensions

set "ROOT=%~dp0"

set "ROOT=%ROOT:~0,-1%"

set "AIAPI=%ROOT%\full-stack-deepagents\ai-api"

set "REQ=%AIAPI%\requirements.txt"

set "VENVPY=%AIAPI%\venv\Scripts\python.exe"



if not exist "%REQ%" (

  echo ERROR: requirements.txt not found:

  echo   %REQ%

  exit /b 1

)



if exist "%VENVPY%" (

  echo Using existing venv: %AIAPI%\venv

  "%VENVPY%" -m pip install -r "%REQ%"

  if errorlevel 1 exit /b 1

  goto :done

)



where python >nul 2>&1

if errorlevel 1 (

  echo ERROR: Python is not on PATH. Install Python 3.10 or newer, then run this script again.

  exit /b 1

)



echo No venv at ai-api\venv — installing into the current Python environment.

echo Tip: run  python -m venv "%AIAPI%\venv"  then re-run this script to use an isolated env ^(matches start-all.bat^).

python -m pip install -r "%REQ%"

if errorlevel 1 exit /b 1



:done

echo.

echo Finished installing full-stack-deepagents\ai-api\requirements.txt

endlocal

exit /b 0
