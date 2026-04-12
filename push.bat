@echo off

setlocal EnableExtensions

cd /d "%~dp0"

REM ## ⬇️ GitHub main only (origin pushurl includes Gitee — avoids only updating Gitee main from here). Then Gitee: main + master via remote.gitee.push.

git push https://github.com/MartinChen1973/lllm.git main

if errorlevel 1 exit /b 1

git push gitee

if errorlevel 1 exit /b 1

endlocal

exit /b 0
