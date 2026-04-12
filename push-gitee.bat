@echo off

setlocal EnableExtensions

cd /d "%~dp0"

REM ## ⬇️ Gitee remote is configured with two push refspecs (main -> main and main -> master). Use plain "git push gitee", not "git push gitee main", or only main moves.

git push gitee

if errorlevel 1 exit /b 1

endlocal

exit /b 0
