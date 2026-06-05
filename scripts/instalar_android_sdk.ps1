# Instala Android SDK (linha de comando) para gerar APK com Flutter.
$ErrorActionPreference = "Stop"
$SdkRoot = "C:\Android\Sdk"
$ZipUrl = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"
$ZipTemp = "$env:TEMP\android-cmdline-tools.zip"

Write-Host "=== Android SDK (linha de comando) ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $SdkRoot | Out-Null

if (-not (Test-Path "$SdkRoot\cmdline-tools\latest\bin\sdkmanager.bat")) {
    Write-Host "Baixando command line tools..."
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipTemp -UseBasicParsing
    $ExtractTemp = "$env:TEMP\android-cmdline-extract"
    if (Test-Path $ExtractTemp) { Remove-Item -Recurse -Force $ExtractTemp }
    Expand-Archive -Path $ZipTemp -DestinationPath $ExtractTemp -Force
    New-Item -ItemType Directory -Force -Path "$SdkRoot\cmdline-tools\latest" | Out-Null
    Copy-Item -Recurse -Force "$ExtractTemp\cmdline-tools\*" "$SdkRoot\cmdline-tools\latest\"
    Remove-Item -Recurse -Force $ExtractTemp, $ZipTemp -ErrorAction SilentlyContinue
}

$SdkManager = "$SdkRoot\cmdline-tools\latest\bin\sdkmanager.bat"
$env:ANDROID_HOME = $SdkRoot
$env:ANDROID_SDK_ROOT = $SdkRoot

Write-Host "Instalando pacotes SDK (pode demorar)..."
& $SdkManager --sdk_root=$SdkRoot "platform-tools" "platforms;android-35" "build-tools;35.0.0" | Out-Host

Write-Host "Aceitando licencas..."
$yes = ("y`n" * 50)
$yes | & $SdkManager --sdk_root=$SdkRoot --licenses 2>&1 | Out-Host

$Flutter = "C:\src\flutter\bin\flutter.bat"
if (Test-Path $Flutter) {
    & $Flutter config --android-sdk $SdkRoot
    Write-Host "Android SDK configurado em $SdkRoot" -ForegroundColor Green
    & $Flutter doctor
} else {
    Write-Host "Configure: flutter config --android-sdk $SdkRoot" -ForegroundColor Yellow
}
