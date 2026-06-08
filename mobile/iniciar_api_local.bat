@echo off
setlocal

set RAIZ=%~dp0..
set PYTHONPATH=%RAIZ%
cd /d "%RAIZ%"

if not exist "%RAIZ%\venv\Scripts\uvicorn.exe" (
    echo Ambiente Python nao encontrado. Execute executar_api.bat uma vez.
    exit /b 1
)

echo Iniciando API em http://127.0.0.1:8000
start "API Financeiro" /MIN "%RAIZ%\venv\Scripts\uvicorn.exe" api.main:app --host 0.0.0.0 --port 8000
