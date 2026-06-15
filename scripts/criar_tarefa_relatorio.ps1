# Cria tarefa do Agendador de Tarefas: a cada 1 minuto, mesmo na bateria.
param(
    [string]$RaizProjeto = (Split-Path $PSScriptRoot -Parent)
)

$ErrorActionPreference = "Stop"

function Test-ExecutandoComoAdmin {
    $principal = New-Object Security.Principal.WindowsPrincipal(
        [Security.Principal.WindowsIdentity]::GetCurrent()
    )
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Remover-TarefaAgendada {
    param([string]$Nome)
    try {
        $tarefa = Get-ScheduledTask -TaskName $Nome -ErrorAction SilentlyContinue
        if ($tarefa) {
            Unregister-ScheduledTask -TaskName $Nome -Confirm:$false -ErrorAction Stop
        }
    }
    catch {
        $null = cmd.exe /c "schtasks /Delete /TN `"$Nome`" /F >nul 2>&1"
    }
}

$nomeTarefa = "FinanceiroAgendadorRelatorio"
$nomeTarefaAntiga = "FinanceiroRelatorioCarteira"
$vbs = Join-Path $RaizProjeto "scripts\executar_relatorio_agendado_oculto.vbs"
$wscript = Join-Path $env:SystemRoot "System32\wscript.exe"
$usuario = "$env:USERDOMAIN\$env:USERNAME"

if (-not (Test-Path $vbs)) {
    throw "Arquivo nao encontrado: $vbs"
}

if (Test-ExecutandoComoAdmin) {
    Write-Host ""
    Write-Host "[AVISO] Este script esta rodando como Administrador." -ForegroundColor Yellow
    Write-Host "        Isso costuma causar 'Acesso negado' na tarefa interativa." -ForegroundColor Yellow
    Write-Host "        Feche e execute com duplo clique NORMAL (sem admin)." -ForegroundColor Yellow
    Write-Host ""
}

$argumentos = "//B //Nologo `"$vbs`""
$descricao = "Verifica a cada minuto os horarios do relatorio automatico da carteira."

foreach ($nomeRemover in @($nomeTarefaAntiga, $nomeTarefa)) {
    Remover-TarefaAgendada -Nome $nomeRemover
}

$criada = $false
$ultimoErro = ""

# Metodo 1: cmdlets nativos do Agendador (melhor para usuario comum, sem admin).
try {
    $acao = New-ScheduledTaskAction -Execute $wscript -Argument $argumentos -WorkingDirectory $RaizProjeto

    $inicio = (Get-Date).Date
    $gatilhoMinuto = New-ScheduledTaskTrigger -Once -At $inicio `
        -RepetitionInterval (New-TimeSpan -Minutes 1) `
        -RepetitionDuration (New-TimeSpan -Days 3650)
    $gatilhoLogon = New-ScheduledTaskTrigger -AtLogOn

    $config = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

    $principal = New-ScheduledTaskPrincipal `
        -UserId $usuario `
        -LogonType Interactive `
        -RunLevel Limited

    Register-ScheduledTask `
        -TaskName $nomeTarefa `
        -Action $acao `
        -Trigger @($gatilhoMinuto, $gatilhoLogon) `
        -Settings $config `
        -Principal $principal `
        -Description $descricao `
        -Force | Out-Null

    $criada = $true
}
catch {
    $ultimoErro = $_.Exception.Message
}

# Metodo 2: schtasks simples (sem XML).
if (-not $criada) {
    $comando = "`"$wscript`" //B //Nologo `"$vbs`""
    $saida = cmd.exe /c "schtasks /Create /TN `"$nomeTarefa`" /TR `"$comando`" /SC MINUTE /MO 1 /ST 00:00 /RL LIMITED /F 2>&1"
    if ($LASTEXITCODE -eq 0) {
        $criada = $true
    }
    else {
        $ultimoErro = if ($saida) { $saida } else { $ultimoErro }
    }
}

if (-not $criada) {
    Write-Host ""
    Write-Host "[ERRO] Nao foi possivel criar a tarefa agendada." -ForegroundColor Red
    Write-Host "Detalhe: $ultimoErro" -ForegroundColor Red
    Write-Host ""
    Write-Host "Tente:" -ForegroundColor Yellow
    Write-Host "  1. Executar com duplo clique (SEM 'Executar como administrador')"
    Write-Host "  2. Abrir taskschd.msc e apagar manualmente FinanceiroRelatorioCarteira"
    Write-Host "  3. Rodar este script de novo"
    Write-Host ""
    exit 1
}

Write-Host "Tarefa criada: $nomeTarefa"
Write-Host "Usuario: $usuario"
Write-Host "Repeticao: a cada 1 minuto (tambem ao fazer logon)"
Write-Host "Bateria: permitido"
