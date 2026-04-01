@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo Starting full-stack-deepagents (AI API -^> Node -^> Next; MCP optional)...
echo Root: %ROOT%

REM 1) FastAPI + deep agent (no MCP required for chat)
if exist "%ROOT%\ai-api\venv\Scripts\python.exe" (
  start "AI API (8500)" /D "%ROOT%\ai-api" "%ROOT%\ai-api\venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8500
) else (
  start "AI API (8500)" /D "%ROOT%\ai-api" cmd /k "uvicorn main:app --host 127.0.0.1 --port 8500"
)
timeout /t 5 /nobreak >nul

REM 2) Node proxy
start "Node backend (3501)" /D "%ROOT%\backend" cmd /k "npm start"
timeout /t 3 /nobreak >nul

REM 3) Next.js
start "Next frontend (3500)" /D "%ROOT%\frontend" cmd /k "npm run dev"
timeout /t 8 /nobreak >nul

REM 4) MCP Streamable HTTP (optional; not used by the AI API until tools are wired)
if exist "%ROOT%\mcp-server\venv\Scripts\python.exe" (
  start "MCP server (8501)" /D "%ROOT%\mcp-server" "%ROOT%\mcp-server\venv\Scripts\python.exe" server.py
) else (
  start "MCP server (8501)" /D "%ROOT%\mcp-server" cmd /k "python server.py"
)

REM ## ⬇️ Tile the four service consoles in a 2x2 grid on the primary monitor (process + title).
timeout /t 4 /nobreak >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\arrange-console-grid.ps1"

REM Open UIs in one new browser window (four tabs only; avoids attaching to an existing window).
REM Optional: set DEEPAGENTS_BROWSER to full path of chrome.exe, msedge.exe, etc. (Chromium-based).
set "BROWSER_EXE="
if defined DEEPAGENTS_BROWSER set "BROWSER_EXE=%DEEPAGENTS_BROWSER%"
if not defined BROWSER_EXE if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "BROWSER_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER_EXE if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "BROWSER_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER_EXE if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "BROWSER_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER_EXE if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "BROWSER_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if defined BROWSER_EXE (
  start "" "%BROWSER_EXE%" --new-window "http://127.0.0.1:8500/docs" "http://127.0.0.1:8501/docs" "http://127.0.0.1:3501/docs" "http://127.0.0.1:3500/"
) else (
  echo WARNING: Edge/Chrome not found in usual paths; opening with default handler ^(may reuse an existing window^).
  start "" "http://127.0.0.1:8500/docs"
  timeout /t 2 /nobreak >nul
  start "" "http://127.0.0.1:8501/docs"
  start "" "http://127.0.0.1:3501/docs"
  start "" "http://127.0.0.1:3500/"
)

echo.
echo One new browser window should show four tabs ^(8500/8501/3501 docs + Next^). Four console windows should be running.
echo Press any key to close this launcher window (servers keep running).
pause >nul
