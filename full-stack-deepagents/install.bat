@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo.
echo === full-stack-deepagents: install (5 ends) ===
echo Root: %ROOT%
echo   1^) ai-api           - Python venv + requirements.txt
echo   2^) mcp-server-rag   - Python venv + FAISS RAG MCP ^(8501^)
echo   3^) mcp-server       - Python venv + auxiliary MCP ^(8502^)
echo   4^) backend          - npm install
echo   5^) frontend         - npm install
echo.

REM ## ⬇️ Resolve Python 3 (python.exe or py -3 launcher)
set "PY=python"
%PY% --version >nul 2>&1
if errorlevel 1 set "PY=py -3"
%PY% --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python 3 is required. Install from https://www.python.org/downloads/ or enable the "py" launcher.
  exit /b 1
)
for /f "tokens=*" %%i in ('%PY% -c "import sys; print(sys.executable)"') do set "PY_EXE=%%i"
echo Using Python: %PY_EXE%
echo.

where npm >nul 2>&1
if errorlevel 1 (
  echo ERROR: npm is required. Install Node.js from https://nodejs.org/
  exit /b 1
)

REM ## ⬇️ ai-api: create venv if missing, then install dependencies
echo [1/5] ai-api...
if not exist "%ROOT%\ai-api\venv\Scripts\python.exe" (
  echo   Creating venv "%ROOT%\ai-api\venv"...
  %PY% -m venv "%ROOT%\ai-api\venv"
  if errorlevel 1 exit /b 1
)
"%ROOT%\ai-api\venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%ROOT%\ai-api\venv\Scripts\python.exe" -m pip install -r "%ROOT%\ai-api\requirements.txt"
if errorlevel 1 exit /b 1
echo   OK.
echo.

REM ## ⬇️ mcp-server-rag: create venv if missing, then install dependencies
echo [2/5] mcp-server-rag...
if not exist "%ROOT%\mcp-server-rag\venv\Scripts\python.exe" (
  echo   Creating venv "%ROOT%\mcp-server-rag\venv"...
  %PY% -m venv "%ROOT%\mcp-server-rag\venv"
  if errorlevel 1 exit /b 1
)
"%ROOT%\mcp-server-rag\venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%ROOT%\mcp-server-rag\venv\Scripts\python.exe" -m pip install -r "%ROOT%\mcp-server-rag\requirements.txt"
if errorlevel 1 exit /b 1
echo   OK.
echo.

REM ## ⬇️ mcp-server: auxiliary Streamable HTTP MCP (default port 8502)
echo [3/5] mcp-server...
if not exist "%ROOT%\mcp-server\venv\Scripts\python.exe" (
  echo   Creating venv "%ROOT%\mcp-server\venv"...
  %PY% -m venv "%ROOT%\mcp-server\venv"
  if errorlevel 1 exit /b 1
)
"%ROOT%\mcp-server\venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%ROOT%\mcp-server\venv\Scripts\python.exe" -m pip install -r "%ROOT%\mcp-server\requirements.txt"
if errorlevel 1 exit /b 1
echo   OK.
echo.

REM ## ⬇️ Node backend
echo [4/5] backend ^(npm^)...
pushd "%ROOT%\backend"
call npm install
if errorlevel 1 (
  popd
  exit /b 1
)
popd
echo   OK.
echo.

REM ## ⬇️ Next.js frontend
echo [5/5] frontend ^(npm^)...
pushd "%ROOT%\frontend"
call npm install
if errorlevel 1 (
  popd
  exit /b 1
)
popd
echo   OK.
echo.

echo All five ends are installed.
echo Run start-all.bat from this folder to launch services ^(start-all uses venv Python when present^).
echo.
exit /b 0
