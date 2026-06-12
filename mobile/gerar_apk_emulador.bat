@echo off
setlocal EnableDelayedExpansion

set ORIGEM=%~dp0financeiro_app
set FLUTTER=C:\src\flutter\bin\flutter.bat
set WORK_TEMP=C:\temp\financeiro_apk_work
set PROJETO=%WORK_TEMP%\financeiro_app

if not exist "%FLUTTER%" (
    echo Flutter nao encontrado. Execute primeiro:
    echo   powershell -ExecutionPolicy Bypass -File "%~dp0..\scripts\instalar_flutter.ps1"
    if /I not "%~1"=="auto" pause
    exit /b 1
)

if not defined JAVA_HOME (
    if exist "C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot\bin\java.exe" (
        set "JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot"
    ) else (
        for /d %%J in ("C:\Program Files\Microsoft\jdk-*") do (
            if exist "%%J\bin\java.exe" set "JAVA_HOME=%%J"
        )
        if not defined JAVA_HOME (
            for /d %%J in ("C:\Program Files\Java\jdk-*") do (
                if exist "%%J\bin\java.exe" set "JAVA_HOME=%%J"
            )
        )
    )
)

if not defined JAVA_HOME (
    echo JDK nao encontrado. Instale: winget install Microsoft.OpenJDK.17
    if /I not "%~1"=="auto" pause
    exit /b 1
)

set "PATH=%JAVA_HOME%\bin;%PATH%"

if not defined ANDROID_HOME (
    if exist "C:\Android\Sdk\platform-tools\adb.exe" (
        set "ANDROID_HOME=C:\Android\Sdk"
    )
)
if defined ANDROID_HOME (
    set "ANDROID_SDK_ROOT=%ANDROID_HOME%"
    set "PATH=%ANDROID_HOME%\platform-tools;%PATH%"
)
set "GRADLE_USER_HOME=C:\temp\financeiro_gradle_user"

if not exist "%WORK_TEMP%" mkdir "%WORK_TEMP%"

if exist "%PROJETO%" (
    echo Removendo copia anterior em %WORK_TEMP%...
    rmdir /s /q "%PROJETO%" 2>nul
)

echo.
echo Copiando projeto para build local...
robocopy "%ORIGEM%" "%PROJETO%" /E /XD build .dart_tool android\.gradle android\app\build ios\Flutter\ephemeral macos\Flutter\ephemeral linux\flutter\ephemeral windows\flutter\ephemeral /NFL /NDL /NJH /NJS /nc /ns /np >nul
if errorlevel 8 (
    echo Falha ao copiar projeto.
    if /I not "%~1"=="auto" pause
    exit /b 1
)

cd /d "%PROJETO%"

echo Limpando cache de build anterior (garante codigo novo no APK)...
call "%FLUTTER%" clean
if errorlevel 1 (
    echo Falha no flutter clean.
    if /I not "%~1"=="auto" pause
    exit /b 1
)

call "%FLUTTER%" pub get
if errorlevel 1 (
    echo Falha no pub get.
    if /I not "%~1"=="auto" pause
    exit /b 1
)

rem Registrant antigo na pasta temp (robocopy nao apaga) quebra compile apos clean
del /f /q "android\app\src\main\java\io\flutter\plugins\GeneratedPluginRegistrant.java" 2>nul

echo.
echo Gerando APK para emulador (cotacoes direto Yahoo/Brapi)...
call "%FLUTTER%" build apk --release
if errorlevel 1 (
    echo Falha no build.
    if /I not "%~1"=="auto" pause
    exit /b 1
)

set APK_BUILD=%PROJETO%\build\app\outputs\flutter-apk\app-release.apk
set APK_NOME=Financeiro-emulador.apk
set APK_DEST=%~dp0%APK_NOME%
set APK_COPIA_PROJETO=%ORIGEM%\%APK_NOME%

copy /Y "%APK_BUILD%" "%APK_DEST%" >nul
copy /Y "%APK_BUILD%" "%APK_COPIA_PROJETO%" >nul

echo.
echo APK emulador gerado: %APK_DEST%
echo Use com: testar_apk.bat
if /I not "%~1"=="auto" pause
exit /b 0
