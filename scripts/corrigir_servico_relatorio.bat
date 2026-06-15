@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo ============================================
echo  Corrigir servico de relatorio da carteira
echo ============================================
echo.
echo Erro 1069 = senha errada ou falta permissao "Iniciar sessao como servico".
echo Erro 1053 = Sistema Local nao acessa pasta no OneDrive.
echo.
echo RECOMENDADO: ignore o servico e use:
echo   scripts\ativar_relatorio_automatico.bat
echo (ja funciona sem admin e sem senha de servico)
echo.
echo Deseja tentar corrigir o servico Windows mesmo assim? (S/N)
set /p CONTINUAR=
if /I not "%CONTINUAR%"=="S" (
    echo Use scripts\ativar_relatorio_automatico.bat
    pause
    exit /b 0
)

net session >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Execute como Administrador.
    pause
    exit /b 1
)

sc.exe query FinanceiroRelatorioCarteira >nul 2>&1
if errorlevel 1 (
    echo Servico nao encontrado. Execute instalar_servico_relatorio.bat
    pause
    exit /b 1
)

set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
set "SCRIPT_SERVICO=%CD%\src\Service\servico_relatorio_windows.py"
set "CONTA=%USERDOMAIN%\%USERNAME%"

echo.
echo Conta: %CONTA%
echo Digite a senha do Windows (conta Microsoft: senha da conta, nao o PIN):
set /p SENHA_SERVICO=

if "%SENHA_SERVICO%"=="" (
    echo [ERRO] Senha nao informada.
    pause
    exit /b 1
)

echo.
echo Concedendo permissao "Iniciar sessao como servico"...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0conceder_logon_servico.ps1" -Usuario "%CONTA%"
if errorlevel 1 (
    echo Aviso: nao foi possivel conceder permissao automaticamente.
)

echo Parando servico...
sc.exe stop FinanceiroRelatorioCarteira >nul 2>&1
timeout /t 2 /nobreak >nul

echo Reconfigurando servico com sua conta...
"%PYTHON_EXE%" "%SCRIPT_SERVICO%" --username "%CONTA%" --password "%SENHA_SERVICO%" update
sc.exe config FinanceiroRelatorioCarteira obj= "%CONTA%" password= "%SENHA_SERVICO%"

echo Iniciando servico...
sc.exe start FinanceiroRelatorioCarteira
if errorlevel 1 (
    echo.
    echo Ainda nao iniciou. Use o agendador:
    echo   scripts\ativar_relatorio_automatico.bat
    echo E remova o servico: scripts\desinstalar_servico_relatorio.bat
    pause
    exit /b 1
)

echo.
echo Servico iniciado.
pause
