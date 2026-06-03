# Script de desenvolvimento - Financeiro (desktop Python)
# Uso: .\scripts\desenvolver.ps1

$ErroPreferencia = $ErrorActionPreference
$ErrorActionPreference = "Stop"

$RaizProjeto = Split-Path -Parent $PSScriptRoot
Set-Location $RaizProjeto

Write-Host "=== Financeiro - Aplicacao Desktop Python ===" -ForegroundColor Cyan
Write-Host "Pasta: $RaizProjeto"

$Venv = Join-Path $RaizProjeto "venv"
if (-not (Test-Path $Venv)) {
    Write-Host "Criando ambiente virtual Python..." -ForegroundColor Yellow
    python -m venv $Venv
}

$Python = Join-Path $Venv "Scripts\python.exe"
$Pip = Join-Path $Venv "Scripts\pip.exe"

if (-not (Test-Path $Python)) {
    Write-Host "Python nao encontrado. Instale Python 3.10+." -ForegroundColor Red
    exit 1
}

Write-Host "Instalando dependencias..." -ForegroundColor Yellow
& $Pip install -r (Join-Path $RaizProjeto "requirements.txt") --quiet

$PastaLog = Join-Path $RaizProjeto "log"
if (-not (Test-Path $PastaLog)) {
    New-Item -ItemType Directory -Path $PastaLog | Out-Null
}

$env:PYTHONPATH = $RaizProjeto

Write-Host ""
Write-Host "Abrindo janela do Financeiro..." -ForegroundColor Green
Write-Host ""

& $Python -m src.main

$ErrorActionPreference = $ErroPreferencia
