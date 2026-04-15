@echo off
setlocal
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -NoExit -File "%SCRIPT_DIR%start-wenxian-dev.ps1"
