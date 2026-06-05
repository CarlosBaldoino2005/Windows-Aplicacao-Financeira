# Instala Flutter SDK (stable) e prepara PATH para esta sessao.
# Execute no PowerShell:  .\scripts\instalar_flutter.ps1

$ErrorActionPreference = "Stop"
$PastaFlutter = "C:\src\flutter"

Write-Host "=== Instalador Flutter (Financeiro) ===" -ForegroundColor Cyan

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git nao encontrado. Instale: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "$PastaFlutter\bin\flutter.bat")) {
    Write-Host "Baixando Flutter stable em $PastaFlutter ..."
    New-Item -ItemType Directory -Force -Path (Split-Path $PastaFlutter) | Out-Null
    if (Test-Path $PastaFlutter) {
        Remove-Item -Recurse -Force $PastaFlutter
    }
    git clone https://github.com/flutter/flutter.git -b stable --depth 1 $PastaFlutter
} else {
    Write-Host "Flutter ja existe em $PastaFlutter"
}

$env:Path = "$PastaFlutter\bin;" + $env:Path

# PATH permanente do usuario (se ainda nao estiver)
$EntradaPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($EntradaPath -notlike "*$PastaFlutter\bin*") {
    [Environment]::SetEnvironmentVariable("Path", "$PastaFlutter\bin;$EntradaPath", "User")
    Write-Host "PATH do usuario atualizado (feche e reabra o terminal depois)." -ForegroundColor Green
}

Write-Host "`nVerificando instalacao (flutter doctor)..." -ForegroundColor Cyan
flutter doctor

Write-Host "`n=== Proximo passo (app Android) ===" -ForegroundColor Yellow
Write-Host @"

1. Instale Android Studio: https://developer.android.com/studio
2. No Android Studio: SDK Manager -> Android SDK + Platform-Tools
3. Aceite licencas:
   flutter doctor --android-licenses
4. Gere o projeto e o APK:
   cd mobile\financeiro_app
   flutter create . --project-name financeiro_app --org br.com.financeiro
   flutter pub get
   flutter build apk --release

APK: mobile\financeiro_app\build\app\outputs\flutter-apk\app-release.apk

"@
