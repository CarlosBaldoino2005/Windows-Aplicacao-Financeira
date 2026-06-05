@echo off

cd /d "%~dp0financeiro_app"

set FLUTTER=C:\src\flutter\bin\flutter.bat



if not exist "%FLUTTER%" (

    echo Flutter nao encontrado. Execute primeiro:

    echo   powershell -ExecutionPolicy Bypass -File "%~dp0..\scripts\instalar_flutter.ps1"

    pause

    exit /b 1

)



if not exist "android\app\build.gradle" (

    echo Gerando pastas Android...

    call "%FLUTTER%" create . --project-name financeiro_app --org br.com.financeiro

)



call "%FLUTTER%" pub get

call "%FLUTTER%" doctor



echo.

echo Se aparecer erro "Android SDK", instale o Android Studio:

echo https://developer.android.com/studio

echo Depois: flutter doctor --android-licenses

echo.

set /p CONTINUAR="Tentar gerar APK mesmo assim? (S/N): "

if /i not "%CONTINUAR%"=="S" exit /b 0



call "%FLUTTER%" build apk --release

if errorlevel 1 (

    echo.

    echo Falha no build. Instale Android Studio e aceite as licencas.

    pause

    exit /b 1

)



echo.

echo APK gerado em:

echo %cd%\build\app\outputs\flutter-apk\app-release.apk

pause

