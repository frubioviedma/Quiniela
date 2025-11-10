@echo off
setlocal
echo == Quiniela Pro - Lanzador de desarrollo ==
set QUINIELA_DEV_MODE=1

set ROOT=%~dp0
set SCRIPT=%ROOT%scripts\run_app.py

if not exist "%SCRIPT%" (
  echo No se encontro scripts\run_app.py
  exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
  py -3 "%SCRIPT%" %*
) else (
  python "%SCRIPT%" %*
)
exit /b %ERRORLEVEL%

