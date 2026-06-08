@echo off
setlocal EnableDelayedExpansion

set AVD=Financeiro_Emulador
set ANDROID_HOME=C:\Android\Sdk
set EMULATOR=%ANDROID_HOME%\emulator\emulator.exe
set ADB=%ANDROID_HOME%\platform-tools\adb.exe
set ARGS=-avd %AVD% -no-snapshot-load -no-boot-anim -gpu swiftshader_indirect -memory 4096

if not exist "%EMULATOR%" (
    echo Emulador Android nao encontrado em %ANDROID_HOME%
    pause
    exit /b 1
)

set "ANDROID_SDK_ROOT=%ANDROID_HOME%"
set "PATH=%ANDROID_HOME%\platform-tools;%ANDROID_HOME%\emulator;%PATH%"

"%EMULATOR%" -list-avds | findstr /X /C:"%AVD%" >nul
if errorlevel 1 (
    echo AVD "%AVD%" nao encontrado.
    pause
    exit /b 1
)

set PROC=0
tasklist /FI "IMAGENAME eq emulator.exe" 2>nul | find /I "emulator.exe" >nul
if not errorlevel 1 set PROC=1

set ADB_DEV=0
if exist "%ADB%" (
    "%ADB%" devices 2>nul | findstr /R "emulator-[0-9]* device" >nul
    if not errorlevel 1 set ADB_DEV=1
)

REM Processo rodando e adb online = emulador de verdade
if !PROC!==1 if !ADB_DEV!==1 (
    echo Emulador ja esta em execucao.
    exit /b 0
)

REM Processo rodando mas adb ainda nao pronto = boot em andamento
if !PROC!==1 (
    echo Emulador esta iniciando. Aguarde a tela do Android.
    exit /b 0
)

REM adb fantasma: lista dispositivo sem processo do emulador
if !ADB_DEV!==1 (
    echo Limpando conexao antiga do adb...
    "%ADB%" kill-server >nul 2>&1
    "%ADB%" start-server >nul 2>&1
)

echo Abrindo emulador %AVD%...
echo Aguarde a tela inicial do Android aparecer (2 a 3 min na primeira vez).
start "" "%EMULATOR%" %ARGS%
