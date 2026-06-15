@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo ==============================================
echo  Desinstalar servico de relatorio da carteira
echo ==============================================
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo Execute este arquivo como Administrador.
    pause
    exit /b 1
)

set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
set "SCRIPT_SERVICO=%CD%\src\Service\servico_relatorio_windows.py"

if not exist "%PYTHON_EXE%" (
    echo Ambiente virtual nao encontrado. Removendo servico via sc...
    sc stop FinanceiroRelatorioCarteira >nul 2>&1
    sc delete FinanceiroRelatorioCarteira >nul 2>&1
    echo Concluido.
    pause
    exit /b 0
)

echo Parando servico...
"%PYTHON_EXE%" "%SCRIPT_SERVICO%" stop >nul 2>&1

echo Removendo servico...
"%PYTHON_EXE%" "%SCRIPT_SERVICO%" remove

echo Servico removido.
pause
