@echo off
rem Quick launcher for showcase pages: run buttons | run notify --topmost | run list
setlocal
cd /d "%~dp0"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0dev\launch.py" %*
endlocal & exit /b %ERRORLEVEL%
