@echo off
setlocal EnableDelayedExpansion

set NOME_ATALHO=Financeiro Emulador
set AVD=Financeiro_Emulador
set ANDROID_HOME=C:\Android\Sdk
set EMULATOR=%ANDROID_HOME%\emulator\emulator.exe
set LAUNCHER=%~dp0abrir_emulador.bat
set PASTA_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Financeiro
set ATALHO=%PASTA_MENU%\%NOME_ATALHO%.lnk

if not exist "%EMULATOR%" (
    echo Emulador nao encontrado em %ANDROID_HOME%
    echo Instale o Android SDK antes de fixar no Menu Iniciar.
    pause
    exit /b 1
)

if not exist "%LAUNCHER%" (
    echo Arquivo nao encontrado: %LAUNCHER%
    pause
    exit /b 1
)

if not exist "%PASTA_MENU%" mkdir "%PASTA_MENU%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%ATALHO%');" ^
  "$s.TargetPath = '%LAUNCHER%';" ^
  "$s.WorkingDirectory = '%~dp0';" ^
  "$s.Arguments = '';" ^
  "$s.Description = 'Abre o emulador Android Financeiro (%AVD%)';" ^
  "if (Test-Path '%EMULATOR%') { $s.IconLocation = '%EMULATOR%,0' };" ^
  "$s.Save()"

if errorlevel 1 (
    echo Falha ao criar atalho no Menu Iniciar.
    pause
    exit /b 1
)

echo Atalho criado no Menu Iniciar:
echo   %ATALHO%
echo.
echo Procure por "%NOME_ATALHO%" no Menu Iniciar.
echo Para fixar no Iniciar: clique com o botao direito no atalho ^> Fixar em Iniciar.
echo.
pause
