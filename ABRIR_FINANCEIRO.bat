@echo off
title Financeiro
cd /d "%~dp0"
echo === Financeiro - Painel de Mercado ===
if not exist "venv\Scripts\python.exe" (
    echo Criando venv...
    python -m venv venv
)
venv\Scripts\pip.exe install -r requirements.txt -q
set PYTHONPATH=%~dp0
venv\Scripts\python.exe -m src.main
if errorlevel 1 (
    echo.
    echo Erro ao abrir. Pressione uma tecla para fechar.
    pause
)
