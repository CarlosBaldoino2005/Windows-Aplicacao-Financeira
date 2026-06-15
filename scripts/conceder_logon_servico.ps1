# Concede "Iniciar sessao como servico" (SeServiceLogonRight) a um usuario local.
param(
    [Parameter(Mandatory = $true)]
    [string]$Usuario
)

$ErrorActionPreference = "Stop"

$conta = New-Object System.Security.Principal.NTAccount($Usuario)
$sid = $conta.Translate([System.Security.Principal.SecurityIdentifier]).Value

$arquivoCfg = Join-Path $env:TEMP ("secpol_{0}.cfg" -f [guid]::NewGuid().ToString("N"))
$arquivoDb = Join-Path $env:TEMP ("secedit_{0}.sdb" -f [guid]::NewGuid().ToString("N"))

try {
    secedit /export /cfg $arquivoCfg /quiet | Out-Null
    if (-not (Test-Path $arquivoCfg)) {
        throw "Nao foi possivel exportar politica de seguranca."
    }

    $linhas = Get-Content $arquivoCfg -Encoding Unicode
    $indicePrivilegios = [array]::IndexOf($linhas, "[Privilege Rights]")
    if ($indicePrivilegios -lt 0) {
        throw "Secao [Privilege Rights] nao encontrada."
    }

  $indiceLinha = -1
    for ($i = $indicePrivilegios + 1; $i -lt $linhas.Count; $i++) {
        if ($linhas[$i] -match '^\[') { break }
        if ($linhas[$i] -match '^SeServiceLogonRight\s*=') {
            $indiceLinha = $i
            break
        }
    }

    $marcadorSid = "*$sid"
    if ($indiceLinha -ge 0) {
        if ($linhas[$indiceLinha] -notmatch [regex]::Escape($sid)) {
            $linhas[$indiceLinha] = ($linhas[$indiceLinha].TrimEnd() + ",$marcadorSid")
        }
    }
    else {
        $antes = $linhas[0..$indicePrivilegios]
        $depois = $linhas[($indicePrivilegios + 1)..($linhas.Count - 1)]
        $linhas = $antes + ("SeServiceLogonRight = {0}" -f $marcadorSid) + $depois
    }

    Set-Content -Path $arquivoCfg -Value $linhas -Encoding Unicode
    secedit /configure /db $arquivoDb /cfg $arquivoCfg /areas USER_RIGHTS /quiet | Out-Null
    Write-Host "Permissao concedida para: $Usuario"
}
finally {
    Remove-Item $arquivoCfg -Force -ErrorAction SilentlyContinue
    Remove-Item $arquivoDb -Force -ErrorAction SilentlyContinue
}
