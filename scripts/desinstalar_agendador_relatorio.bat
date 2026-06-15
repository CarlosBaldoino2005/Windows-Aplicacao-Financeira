@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo Removendo tarefas do agendador de relatorio...
schtasks /Delete /TN "FinanceiroAgendadorRelatorio" /F >nul 2>&1
schtasks /Delete /TN "FinanceiroRelatorioCarteira" /F >nul 2>&1
echo Concluido.
pause
