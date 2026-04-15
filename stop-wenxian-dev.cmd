@echo off
setlocal
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -NoExit -File "%SCRIPT_DIR%stop-wenxian-dev.ps1"
