@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo Removendo tarefa FinanceiroRelatorioCarteira...
schtasks /Delete /TN "FinanceiroRelatorioCarteira" /F
echo Concluido.
pause
