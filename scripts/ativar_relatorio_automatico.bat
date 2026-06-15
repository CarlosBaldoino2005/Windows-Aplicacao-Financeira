@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo =========================================================
echo  Ativar relatorio automatico (recomendado)
echo =========================================================
echo.
echo Usa o Agendador de Tarefas do Windows:
echo   - funciona com pasta no OneDrive
echo   - nao precisa senha de servico nem administrador
echo   - roda com o app fechado, sem janela visivel
echo   - verifica horarios a cada 1 minuto
echo.

call "%~dp0instalar_agendador_relatorio.bat"
if errorlevel 1 exit /b 1

echo.
echo Testando execucao uma vez (verifique log\log-dd-mm-aaaa.log)...
if exist "venv\Scripts\pythonw.exe" (
    start "" /B "venv\Scripts\pythonw.exe" "src\Tool\relatorio_agendado_runner.py"
)

echo.
echo Pronto. O servico Windows NAO e necessario.
echo Se ele existir e der erro 1069/1053, ignore ou remova com:
echo   scripts\desinstalar_servico_relatorio.bat ^(como admin^)
echo.
pause
