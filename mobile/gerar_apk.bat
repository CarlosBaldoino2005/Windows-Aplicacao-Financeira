@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0financeiro_app"

set FLUTTER=C:\src\flutter\bin\flutter.bat

if not exist "%FLUTTER%" (
    echo Flutter nao encontrado. Execute primeiro:
    echo   powershell -ExecutionPolicy Bypass -File "%~dp0..\scripts\instalar_flutter.ps1"
    pause
    exit /b 1
)

REM --- Java (JDK) necessario para o Gradle ---
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
    echo.
    echo JDK nao encontrado. Instale o Java 17:
    echo   winget install Microsoft.OpenJDK.17
    echo.
    echo Depois feche e abra o terminal, ou defina JAVA_HOME manualmente.
    pause
    exit /b 1
)

set "PATH=%JAVA_HOME%\bin;%PATH%"

REM --- Android SDK ---
if not defined ANDROID_HOME (
    if exist "C:\Android\Sdk\platform-tools\adb.exe" (
        set "ANDROID_HOME=C:\Android\Sdk"
    )
)
if defined ANDROID_HOME (
    set "ANDROID_SDK_ROOT=%ANDROID_HOME%"
    set "PATH=%ANDROID_HOME%\platform-tools;%PATH%"
)

if not exist "android\app\build.gradle.kts" if not exist "android\app\build.gradle" (
    echo Gerando pastas Android...
    call "%FLUTTER%" create . --project-name financeiro_app --org br.com.financeiro
)

call "%FLUTTER%" pub get

echo.
echo JAVA_HOME=%JAVA_HOME%
if defined ANDROID_HOME echo ANDROID_HOME=%ANDROID_HOME%
echo.

"%JAVA_HOME%\bin\java.exe" -version 2>&1
if errorlevel 1 (
    echo Falha ao executar java. Verifique o JDK.
    pause
    exit /b 1
)

call "%FLUTTER%" doctor

echo.
echo Gerando APK release...
call "%FLUTTER%" build apk --release

if errorlevel 1 (
    echo.
    echo Falha no build.
    echo Verifique: JAVA_HOME, Android SDK e licencas:
    echo   flutter doctor --android-licenses
    pause
    exit /b 1
)

echo.
echo APK gerado em:
echo %cd%\build\app\outputs\flutter-apk\app-release.apk
pause
