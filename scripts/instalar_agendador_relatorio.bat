@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo =========================================================
echo  Agendador de relatorio da carteira (recomendado)
echo =========================================================
echo.
echo Nao precisa ser administrador. Funciona com o app fechado.
echo Verifica a cada 1 minuto os horarios em dados/painel.ini
echo Execucao 100%% oculta (sem janela do Prompt).
echo.

if not exist "venv\Scripts\pythonw.exe" (
    echo Criando ambiente virtual...
    python -m venv venv
    venv\Scripts\pip.exe install -r requirements.txt
)

set "NOME_TAREFA=FinanceiroRelatorioCarteira"
set "LAUNCHER=%CD%\scripts\executar_relatorio_agendado_oculto.vbs"
set "WSCRIPT=%SystemRoot%\System32\wscript.exe"
set "COMANDO=%WSCRIPT% //B //Nologo %LAUNCHER%"

echo Removendo tarefa anterior, se existir...
schtasks /Delete /TN "%NOME_TAREFA%" /F >nul 2>&1

echo Criando tarefa oculta no Agendador de Tarefas...
schtasks /Create /TN "%NOME_TAREFA%" /TR "%COMANDO%" /SC MINUTE /MO 1 /F
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao criar a tarefa no Agendador.
    pause
    exit /b 1
)

echo.
echo Tarefa instalada com sucesso (sem janela visivel).
echo Nome: %NOME_TAREFA%
echo Onde ver: Win+R ^> taskschd.msc ^> Biblioteca do Agendador de Tarefas
echo.
echo Horarios e e-mails: configuracao da carteira ^(dados/painel.ini^)
echo SMTP: dados/email.ini
echo Logs: log\log-dd-mm-aaaa.log
echo.
pause
