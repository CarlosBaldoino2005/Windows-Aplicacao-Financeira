@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo ============================================
echo  Diagnostico do agendador de relatorio
echo ============================================
echo.

set "TAREFA=FinanceiroAgendadorRelatorio"
schtasks /Query /TN "%TAREFA%" /FO LIST /V 2>nul | findstr /I "Nome da tarefa Status Tipo Repetir proxima ultima resultador bateria Tarefa a ser"
if errorlevel 1 (
    echo Tarefa %TAREFA% nao encontrada.
    schtasks /Query /TN "FinanceiroRelatorioCarteira" /FO LIST /V 2>nul | findstr /I "Nome da tarefa Status Tipo Repetir proxima ultima resultador bateria Tarefa a ser"
    if not errorlevel 1 (
        echo.
        echo AVISO: tarefa antiga encontrada. Execute instalar_agendador_relatorio.bat
    )
)

echo.
echo Configuracao em dados\painel.ini:
findstr /I "carteira_relatorio" dados\painel.ini 2>nul

echo.
echo Ultimas linhas do log de hoje:
for /f "delims=" %%L in ('powershell -NoProfile -Command "Get-Date -Format 'dd-MM-yyyy'"') do set "HOJE=%%L"
set "LOG=log\log-%HOJE%.log"
if exist "%LOG%" (
    powershell -NoProfile -Command "Get-Content -Path '%LOG%' -Tail 12 -ErrorAction SilentlyContinue"
) else (
    echo Arquivo nao encontrado: %LOG%
    echo O agendador ainda nao gravou log hoje.
)

echo.
echo Executando verificacao manual agora...
start "" /B "venv\Scripts\pythonw.exe" "src\Tool\relatorio_agendado_runner.py"
echo Aguarde 5 segundos e confira o log novamente.
timeout /t 5 /nobreak >nul

if exist "%LOG%" (
    powershell -NoProfile -Command "Get-Content -Path '%LOG%' -Tail 5 -ErrorAction SilentlyContinue"
)

echo.
pause
