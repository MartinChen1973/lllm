@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo Starting full-stack-deepagents (MCP OA + Bingchuan, then AI API; Node -^> Next)...
echo Root: %ROOT%

REM 1) MCP OA FAISS (8501) — folder: mcp-server-oa (lookup_docs; ai-api default MCP_OA_URL)
REM ## ⬇️ cmd /k + title keeps the taskbar/console label readable (direct python.exe titles often show only the .exe path).
if exist "%ROOT%\mcp-server-oa\venv\Scripts\python.exe" (
  start "MCP OA (8501)" /D "%ROOT%\mcp-server-oa" cmd /k "title MCP OA (8501) & venv\Scripts\python.exe server.py"
) else (
  start "MCP OA (8501)" /D "%ROOT%\mcp-server-oa" cmd /k "title MCP OA (8501) & python server.py"
)
timeout /t 2 /nobreak >nul

REM 2) MCP Bingchuan FAISS (8503) — default port set so it does not collide with OA (8501) or aux (8502)
if exist "%ROOT%\mcp-server-bingchuan\venv\Scripts\python.exe" (
  REM ## ⬇️ Use cwd-relative venv path after /D — nested ""quotes"" around %ROOT%\...\python.exe can make cmd run `python` with the .exe as a script (SyntaxError on \x90).
  start "MCP Bingchuan (8503)" /D "%ROOT%\mcp-server-bingchuan" cmd /k "title MCP Bingchuan (8503) & set MCP_PORT=8503&& venv\Scripts\python.exe server.py"
) else (
  start "MCP Bingchuan (8503)" /D "%ROOT%\mcp-server-bingchuan" cmd /k "title MCP Bingchuan (8503) & set MCP_PORT=8503&& python server.py"
)
timeout /t 2 /nobreak >nul

REM 3) Auxiliary MCP (8502; empty tools demo — optional third connection in ai-api)
if exist "%ROOT%\mcp-server\venv\Scripts\python.exe" (
  start "MCP aux (8502)" /D "%ROOT%\mcp-server" cmd /k "title MCP aux (8502) & venv\Scripts\python.exe server.py"
) else (
  start "MCP aux (8502)" /D "%ROOT%\mcp-server" cmd /k "title MCP aux (8502) & python server.py"
)
timeout /t 3 /nobreak >nul

REM 4) FastAPI + deep agent (loads MCP at process startup)
if exist "%ROOT%\ai-api\venv\Scripts\python.exe" (
  start "AI API (8500)" /D "%ROOT%\ai-api" cmd /k "title AI API (8500) & venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8500"
) else (
  start "AI API (8500)" /D "%ROOT%\ai-api" cmd /k "title AI API (8500) & uvicorn main:app --host 127.0.0.1 --port 8500"
)
timeout /t 5 /nobreak >nul

REM 5) Node proxy
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\warn-if-port-in-use.ps1" -Port 3501 -Hint "Close the old Node backend window or taskkill that PID; then this new instance can bind."
REM ## ⬇️ Avoid npm start here — npm retitles the console ("npm", "npm start"); node keeps the label closer to service.name.
start "Node backend (3501)" /D "%ROOT%\backend" cmd /k "title Node backend (3501) & node server.js"
timeout /t 3 /nobreak >nul

REM 6) Next.js — dev-console-title.js spawns `next dev` but resets Windows title (Next sets "next-server (v…)").
start "Node frontend (3500)" /D "%ROOT%\frontend" cmd /k "title Node frontend (3500) & node dev-console-title.js"

timeout /t 4 /nobreak >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\arrange-console-grid.ps1"

REM ## ⬇️ AI API blocks accept until lifespan finishes (MCP retries, model, SQLite); open browser only after /openapi.json responds
echo Waiting for AI API (8500) before opening docs tabs...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\wait-http-ready.ps1" -Url "http://127.0.0.1:8500/openapi.json" -Label "AI API (8500)" -MaxWaitSec 120
if errorlevel 1 echo WARNING: AI API ^(8500^) did not respond in time; refresh /docs when its console finishes startup.

set "BROWSER_EXE="
if defined DEEPAGENTS_BROWSER set "BROWSER_EXE=%DEEPAGENTS_BROWSER%"
if not defined BROWSER_EXE if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "BROWSER_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER_EXE if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "BROWSER_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER_EXE if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "BROWSER_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER_EXE if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "BROWSER_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if defined BROWSER_EXE (
  start "" "%BROWSER_EXE%" --new-window "http://127.0.0.1:8500/docs" "http://127.0.0.1:8501/docs" "http://127.0.0.1:8502/docs" "http://127.0.0.1:8503/docs" "http://127.0.0.1:3501/docs" "http://127.0.0.1:3500/"
) else (
  echo WARNING: Edge/Chrome not found in usual paths; opening with default handler ^(may reuse an existing window^).
  start "" "http://127.0.0.1:8500/docs"
  timeout /t 2 /nobreak >nul
  start "" "http://127.0.0.1:8501/docs"
  start "" "http://127.0.0.1:8502/docs"
  start "" "http://127.0.0.1:8503/docs"
  start "" "http://127.0.0.1:3501/docs"
  start "" "http://127.0.0.1:3500/"
)

echo.
echo One browser window should show six tabs ^(8500/8501/8502/8503/3501 docs + Next^). Six service consoles should be running.
echo Press any key to close this launcher window (servers keep running).
pause >nul
