@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo =========================================================
echo  Agendador de relatorio da carteira (recomendado)
echo =========================================================
echo.
echo No PowerShell use UM destes comandos:
echo   cmd /c "%~f0"
echo   .\scripts\instalar_agendador_relatorio.ps1
echo NAO use: md /c ...  ^(md no PowerShell e mkdir, nao cmd^)
echo.
echo Nao precisa ser administrador. Funciona com o app fechado.
echo IMPORTANTE: execute com duplo clique normal. NAO use "Executar como administrador".
echo Verifica a cada 1 minuto os horarios em dados/painel.ini
echo Execucao 100%% oculta (sem janela do Prompt).
echo.

net session >nul 2>&1
if not errorlevel 1 (
    echo [AVISO] Janela aberta como Administrador. Isso pode causar "Acesso negado".
    echo Feche e execute de novo com duplo clique normal ^(sem admin^).
    echo.
    choice /C SN /M "Continuar mesmo assim"
    if errorlevel 2 exit /b 1
    echo.
)

if not exist "venv\Scripts\pythonw.exe" (
    echo Criando ambiente virtual...
    python -m venv venv
    venv\Scripts\pip.exe install -r requirements.txt
)

echo Criando tarefa no Agendador (a cada 1 minuto, inclusive na bateria)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0criar_tarefa_relatorio.ps1" -RaizProjeto "%CD%"
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao criar a tarefa no Agendador.
    echo Dica: execute com duplo clique normal, SEM administrador.
    pause
    exit /b 1
)

echo.
echo Tarefa instalada com sucesso.
echo Nome: FinanceiroAgendadorRelatorio
echo Onde ver: Win+R ^> taskschd.msc ^> Biblioteca do Agendador de Tarefas
echo.
echo Horarios e e-mails: configuracao da carteira ^(dados/painel.ini^)
echo SMTP: dados/email.ini
echo Logs: log\log-dd-mm-aaaa.log
echo.
echo Testando uma execucao agora...
start "" /B "venv\Scripts\pythonw.exe" "src\Tool\relatorio_agendado_runner.py"
echo Aguarde alguns segundos e verifique o arquivo de log de hoje.
echo.
pause
