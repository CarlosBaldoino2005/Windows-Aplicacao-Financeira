# Instala o agendador do relatorio (use no PowerShell: .\scripts\instalar_agendador_relatorio.ps1)
$raiz = Split-Path $PSScriptRoot -Parent
$bat = Join-Path $PSScriptRoot "instalar_agendador_relatorio.bat"

if (-not (Test-Path $bat)) {
    throw "Arquivo nao encontrado: $bat"
}

# Chama o .bat pelo cmd (evita confundir md com mkdir no PowerShell).
$processo = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$bat`"" -WorkingDirectory $raiz -Wait -PassThru
exit $processo.ExitCode
