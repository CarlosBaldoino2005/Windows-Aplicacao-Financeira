@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo Criando venv...
    python -m venv venv
    venv\Scripts\pip.exe install -r requirements.txt
)
set PYTHONPATH=%~dp0
venv\Scripts\python.exe -m src.main
if errorlevel 1 pause
