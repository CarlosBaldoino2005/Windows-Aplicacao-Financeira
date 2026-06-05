@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo Criando venv...
    python -m venv venv
    venv\Scripts\pip.exe install -r requirements.txt -r requirements-api.txt
) else (
    venv\Scripts\pip.exe install -q -r requirements-api.txt
)
set PYTHONPATH=%~dp0
echo API em http://127.0.0.1:8000  —  docs em http://127.0.0.1:8000/docs
venv\Scripts\uvicorn.exe api.main:app --reload --host 0.0.0.0 --port 8000
if errorlevel 1 pause
