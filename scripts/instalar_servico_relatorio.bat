@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo ============================================
echo  Instalar servico de relatorio da carteira
echo  (requer Administrador)
echo ============================================
echo.
echo ATENCAO: projeto em OneDrive costuma falhar como servico Windows.
echo RECOMENDADO: scripts\instalar_agendador_relatorio.bat
echo (nao precisa admin, funciona com app fechado, sem erro 1053).
echo.
echo Continuar com o servico Windows mesmo assim? (S/N)
set /p CONTINUAR=
if /I not "%CONTINUAR%"=="S" (
    echo Cancelado. Use instalar_agendador_relatorio.bat
    pause
    exit /b 0
)
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Execute como Administrador.
    echo Clique direito em instalar_servico_relatorio.bat ^> Executar como administrador
    echo.
    echo Alternativa sem admin: instalar_agendador_relatorio.bat
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv venv
    venv\Scripts\pip.exe install -r requirements.txt
)

set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
set "SCRIPT_SERVICO=%CD%\src\Service\servico_relatorio_windows.py"

echo Projeto: %CD%
echo Python:  %PYTHON_EXE%
echo.

"%PYTHON_EXE%" -c "import win32serviceutil" >nul 2>&1
if errorlevel 1 (
    echo Instalando pywin32...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
)

echo Instalando servico Windows...
"%PYTHON_EXE%" "%SCRIPT_SERVICO%" install
if errorlevel 1 (
    echo.
    echo [ERRO] Falha na instalacao. Mensagem comum: Acesso negado.
    echo Use scripts\instalar_agendador_relatorio.bat ^(nao precisa de admin^).
    pause
    exit /b 1
)

echo Configurando inicio automatico...
"%PYTHON_EXE%" "%SCRIPT_SERVICO%" --startup auto update

echo.
echo IMPORTANTE: pasta no OneDrive exige SUA conta no servico (nao Sistema Local).
echo Digite a senha de login do Windows para o servico rodar com sua conta:
set "CONTA=%USERDOMAIN%\%USERNAME%"
echo Conta: %CONTA%
set /p SENHA_SERVICO=

if "%SENHA_SERVICO%"=="" (
    echo.
    echo Senha nao informada. Servico instalado, mas nao configurado para iniciar.
    echo Execute corrigir_servico_relatorio.bat ou use instalar_agendador_relatorio.bat
    pause
    exit /b 0
)

sc.exe config FinanceiroRelatorioCarteira obj= "%CONTA%" password= "%SENHA_SERVICO%"

echo Iniciando servico...
sc.exe start FinanceiroRelatorioCarteira
if errorlevel 1 (
    echo.
    echo Servico instalado, mas nao iniciou ^(erro 1053 comum no OneDrive^).
    echo Execute corrigir_servico_relatorio.bat ou prefira:
    echo   scripts\instalar_agendador_relatorio.bat
)

echo.
echo Servico instalado.
echo Nome interno: FinanceiroRelatorioCarteira
echo Nome na lista: Financeiro - Relatorio automatico da carteira
echo Abrir: Win+R ^> services.msc
echo.
pause
