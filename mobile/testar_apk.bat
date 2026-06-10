@echo off
setlocal EnableDelayedExpansion

set APK=%~dp0Financeiro-emulador.apk
set AVD=Financeiro_Emulador
set ANDROID_HOME=C:\Android\Sdk
set ANDROID_SDK_ROOT=%ANDROID_HOME%
set ADB=%ANDROID_HOME%\platform-tools\adb.exe
set EMULATOR=%ANDROID_HOME%\emulator\emulator.exe
set BOOT_TMP=%TEMP%\financeiro_boot.txt
set ANIM_TMP=%TEMP%\financeiro_anim.txt
set ARGS_EMU=-avd %AVD% -no-snapshot-load -no-boot-anim -gpu swiftshader_indirect -memory 4096
set RAIZ=%~dp0..
set API_URL=http://127.0.0.1:8000/api/saude

echo Gerando APK atualizado ^(sempre recompila o codigo mais recente^)...
echo A primeira vez ou apos mudancas grandes pode levar 5 a 15 minutos.
echo.
call "%~dp0gerar_apk_emulador.bat" auto
if errorlevel 1 (
    echo Falha ao gerar o APK. Execute manualmente: gerar_apk_emulador.bat
    pause
    exit /b 1
)
if not exist "%APK%" (
    echo APK nao foi criado apos o build.
    pause
    exit /b 1
)
echo APK gerado com sucesso.
echo.

if not exist "%ADB%" (
    echo adb nao encontrado em %ANDROID_HOME%
    pause
    exit /b 1
)

if not exist "%EMULATOR%" (
    echo Emulador Android nao instalado.
    pause
    exit /b 1
)

set "PATH=%ANDROID_HOME%\platform-tools;%ANDROID_HOME%\emulator;%PATH%"

echo === Testar Financeiro.apk no emulador ===
echo.

REM --- API local (emulador usa 127.0.0.1:8000 com adb reverse) ---
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if errorlevel 1 goto subir_api
echo API local ja em execucao.
goto aguardar_api

:subir_api
if exist "%RAIZ%\venv\Scripts\uvicorn.exe" goto api_rapida
echo Criando ambiente Python e API (primeira vez)...
start "API Financeiro" /D "%RAIZ%" cmd /c executar_api.bat
goto aguardar_api

:api_rapida
call "%~dp0iniciar_api_local.bat"

:aguardar_api
echo Aguardando API local em %API_URL% ...
set /a ESPERA_API=0

:loop_api
set /a ESPERA_API+=1
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri '%API_URL%' -UseBasicParsing -TimeoutSec 5).StatusCode | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto api_pronta
if !ESPERA_API! GEQ 40 (
    echo Timeout: API local nao respondeu.
    echo Abra executar_api.bat manualmente e tente de novo.
    pause
    exit /b 1
)
echo   ... aguardando API !ESPERA_API!/40
ping -n 4 127.0.0.1 >nul
goto loop_api

:api_pronta
echo API local pronta.
echo.

REM --- Emulador ---
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
"%ADB%" devices 2>nul | findstr /R "emulator-[0-9]* device" >nul
if not errorlevel 1 set ADB_DEV=1

if !PROC!==0 if !ADB_DEV!==1 (
    echo Limpando conexao antiga do adb...
    "%ADB%" kill-server >nul 2>&1
    "%ADB%" start-server >nul 2>&1
    set ADB_DEV=0
)

if !PROC!==0 if !ADB_DEV!==0 goto iniciar_emulador
if !PROC!==1 if !ADB_DEV!==0 goto emulador_detectado
echo Emulador iniciando. Aguardando conexao com adb...
goto aguardar_adb

:iniciar_emulador
echo Iniciando emulador %AVD%...
echo A primeira abertura pode levar 2 a 3 minutos.
start "" "%EMULATOR%" %ARGS_EMU%
goto aguardar_adb

:emulador_detectado
echo Emulador detectado. Aguardando Android ficar pronto...

:aguardar_adb
echo Aguardando emulador no adb...
set /a ESPERA_ADB=0

:loop_adb
set /a ESPERA_ADB+=1
"%ADB%" devices 2>nul | findstr /R "emulator-[0-9]* device" >nul
if not errorlevel 1 goto adb_pronto
if !ESPERA_ADB! GEQ 90 (
    echo Timeout: emulador nao apareceu em 4 minutos.
    echo Abra pelo atalho Financeiro Emulador no Menu Iniciar e tente de novo.
    pause
    exit /b 1
)
echo   ... aguardando adb !ESPERA_ADB!/90
ping -n 4 127.0.0.1 >nul
goto loop_adb

:adb_pronto
"%ADB%" reverse tcp:8000 tcp:8000 >nul 2>&1
echo Emulador online. Aguardando boot do Android...
set /a TENTATIVAS=0

:loop_boot
set /a TENTATIVAS+=1
set "BOOT="
set "ANIM="

"%ADB%" exec-out getprop sys.boot_completed > "%BOOT_TMP%" 2>nul
if exist "%BOOT_TMP%" for /f "usebackq delims=" %%B in ("%BOOT_TMP%") do set "BOOT=%%B"
if "!BOOT!"=="1" goto boot_pronto

"%ADB%" exec-out getprop init.svc.bootanim > "%ANIM_TMP%" 2>nul
if exist "%ANIM_TMP%" for /f "usebackq delims=" %%A in ("%ANIM_TMP%") do set "ANIM=%%A"
if "!ANIM!"=="stopped" (
    "%ADB%" shell pm path android >nul 2>&1
    if not errorlevel 1 goto boot_pronto
)

if !TENTATIVAS! GEQ 90 (
    echo Timeout: Android nao concluiu o boot em 6 minutos.
    pause
    exit /b 1
)
echo   ... carregando !TENTATIVAS!/90
ping -n 4 127.0.0.1 >nul
goto loop_boot

:boot_pronto
echo Android pronto.
"%ADB%" reverse tcp:8000 tcp:8000 >nul 2>&1
"%ADB%" shell toybox nc -z -w 5 127.0.0.1 8000 >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERRO: emulador nao alcancou a API em 127.0.0.1:8000
    echo Mantenha a janela API Financeiro aberta e execute este script de novo.
    pause
    exit /b 1
)
echo Conexao emulador para API OK.
echo Instalando APK...
"%ADB%" install -r "%APK%"
if errorlevel 1 (
    echo Falha ao instalar o APK.
    pause
    exit /b 1
)

echo Abrindo app Financeiro...
"%ADB%" shell am start -n br.com.financeiro.financeiro_app/.MainActivity

echo.
echo Pronto. O app deve aparecer na janela do emulador.
echo API local: http://127.0.0.1:8000
echo Mantenha a janela API Financeiro aberta enquanto testa.
echo.
pause
