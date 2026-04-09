@echo off

setlocal EnableExtensions

set "ROOT=%~dp0"

set "ROOT=%ROOT:~0,-1%"



echo Starting full-stack-deepagents (MCP OA + Bingchuan, then AI API; Node -^> Next)...

echo Root: %ROOT%



REM 1) MCP OA FAISS (8501) — folder: mcp-servers\mcp-server-oa (lookup_docs; ai-api default MCP_OA_URL)

REM ## ⬇️ cmd /k + title keeps the taskbar/console label readable (direct python.exe titles often show only the .exe path).

if exist "%ROOT%\mcp-servers\mcp-server-oa\venv\Scripts\python.exe" (

  start "MCP OA (8501)" /D "%ROOT%\mcp-servers\mcp-server-oa" cmd /k "title MCP OA (8501) & venv\Scripts\python.exe server.py"

) else (

  start "MCP OA (8501)" /D "%ROOT%\mcp-servers\mcp-server-oa" cmd /k "title MCP OA (8501) & python server.py"

)

timeout /t 2 /nobreak >nul



REM 2) MCP Bingchuan FAISS (8503) — default port set so it does not collide with OA (8501) or aux (8502)

if exist "%ROOT%\mcp-servers\mcp-server-bingchuan\venv\Scripts\python.exe" (

  REM ## ⬇️ Use cwd-relative venv path after /D — nested ""quotes"" around %ROOT%\...\python.exe can make cmd run `python` with the .exe as a script (SyntaxError on \x90).

  start "MCP Bingchuan (8503)" /D "%ROOT%\mcp-servers\mcp-server-bingchuan" cmd /k "title MCP Bingchuan (8503) & set MCP_PORT=8503&& venv\Scripts\python.exe server.py"

) else (

  start "MCP Bingchuan (8503)" /D "%ROOT%\mcp-servers\mcp-server-bingchuan" cmd /k "title MCP Bingchuan (8503) & set MCP_PORT=8503&& python server.py"

)

timeout /t 2 /nobreak >nul



REM 3) Auxiliary MCP (8502; empty tools demo — optional third connection in ai-api)

if exist "%ROOT%\mcp-servers\mcp-server\venv\Scripts\python.exe" (

  start "MCP aux (8502)" /D "%ROOT%\mcp-servers\mcp-server" cmd /k "title MCP aux (8502) & venv\Scripts\python.exe server.py"

) else (

  start "MCP aux (8502)" /D "%ROOT%\mcp-servers\mcp-server" cmd /k "title MCP aux (8502) & python server.py"

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

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\warn-if-port-in-use.ps1" -Port 3501 -Hint "Close the old Node backend window or taskkill that PID; then this new instance can bind."

REM ## ⬇️ Avoid npm start here — npm retitles the console ("npm", "npm start"); node keeps the label closer to service.name.

start "Node backend (3501)" /D "%ROOT%\backend" cmd /k "title Node backend (3501) & node server.js"

timeout /t 3 /nobreak >nul



REM 6) Next.js — dev-console-title.js spawns `next dev` but resets Windows title (Next sets "next-server (v…)").

start "Node frontend (3500)" /D "%ROOT%\frontend" cmd /k "title Node frontend (3500) & node dev-console-title.js"



timeout /t 4 /nobreak >nul

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\arrange-console-grid.ps1"



REM ## ⬇️ AI API blocks accept until lifespan finishes (MCP retries, model, SQLite); open browser only after /openapi.json responds

echo Waiting for AI API (8500) before opening docs tabs (can take up to ~120s while MCP/model/SQLite initialize^)...

echo Do not close this window until you see the browser message below, or tabs will never open.

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\wait-http-ready.ps1" -Url "http://127.0.0.1:8500/openapi.json" -Label "AI API (8500)" -MaxWaitSec 120

if errorlevel 1 echo WARNING: AI API ^(8500^) did not respond in time; opening tabs anyway - refresh /docs when its console finishes startup.



REM ## ⬇️ Use PowerShell Start-Process (registry + standard paths) — cmd "start" + msedge + multiple URLs is easy to mis-parse.

echo Opening documentation tabs...

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\open-local-docs.ps1" "http://127.0.0.1:8500/docs" "http://127.0.0.1:8501/docs" "http://127.0.0.1:8502/docs" "http://127.0.0.1:8503/docs" "http://127.0.0.1:3501/docs" "http://127.0.0.1:3500/"

if errorlevel 1 echo WARNING: open-local-docs.ps1 could not launch a browser; open the URLs above manually.



echo.

echo One browser window should show six tabs ^(8500/8501/8502/8503/3501 docs + Next^). Six service consoles should be running.

echo Press any key to close this launcher window (servers keep running).

pause >nul

