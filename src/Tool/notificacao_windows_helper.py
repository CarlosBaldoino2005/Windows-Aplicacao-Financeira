"""Toast nativo do Windows 10+ para alertas do monitoramento."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from src.Tool.registrar_toast_windows_helper import APP_ID_TOAST

_SCRIPT_TOAST = r"""
param(
    [Parameter(Mandatory = $true)][string]$ArquivoPayload
)
try {
    $payload = Get-Content -LiteralPath $ArquivoPayload -Raw -Encoding UTF8 | ConvertFrom-Json
    $Titulo = [string]$payload.titulo
    $Mensagem = [string]$payload.mensagem
    $AppId = [string]$payload.appId

    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    if ([string]::IsNullOrWhiteSpace($Mensagem)) {
        $tipo = [Windows.UI.Notifications.ToastTemplateType]::ToastText01
    } else {
        $tipo = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
    }
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($tipo)
    $raw = [xml]$template.GetXml()
    ($raw.toast.visual.binding.text | Where-Object { $_.id -eq "1" }).AppendChild($raw.CreateTextNode($Titulo)) | Out-Null
    if (-not [string]::IsNullOrWhiteSpace($Mensagem)) {
        ($raw.toast.visual.binding.text | Where-Object { $_.id -eq "2" }).AppendChild($raw.CreateTextNode($Mensagem)) | Out-Null
    }
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($raw.OuterXml)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($AppId).Show($toast)
    exit 0
} catch {
    exit 1
}
"""


def _enviar_via_powershell(titulo: str, mensagem: str) -> bool:
    caminho_script: Path | None = None
    caminho_payload: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".ps1",
            delete=False,
            encoding="utf-8",
        ) as arquivo:
            arquivo.write(_SCRIPT_TOAST)
            caminho_script = Path(arquivo.name)

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            encoding="utf-8",
        ) as arquivo:
            json.dump(
                {
                    "titulo": titulo,
                    "mensagem": mensagem,
                    "appId": APP_ID_TOAST,
                },
                arquivo,
                ensure_ascii=False,
            )
            caminho_payload = Path(arquivo.name)

        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        resultado = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Sta",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(caminho_script),
                "-ArquivoPayload",
                str(caminho_payload),
            ],
            timeout=20,
            creationflags=flags,
            check=False,
            capture_output=True,
            text=True,
        )
        return resultado.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
    finally:
        for caminho in (caminho_script, caminho_payload):
            if caminho is not None:
                try:
                    caminho.unlink(missing_ok=True)
                except OSError:
                    pass


def _enviar_via_plyer(titulo: str, mensagem: str) -> bool:
    """Fallback: balao na bandeja do sistema (nao exige AppUserModelID)."""
    try:
        from plyer import notification

        titulo_ok = (titulo or "").strip()[:63]
        if not titulo_ok:
            return False
        mensagem_ok = (mensagem or "").strip()
        if not mensagem_ok and len((titulo or "").strip()) > 63:
            mensagem_ok = (titulo or "").strip()[63:255]
        if not mensagem_ok:
            mensagem_ok = "Financeiro"

        notification.notify(
            title=titulo_ok,
            message=mensagem_ok[:255],
            app_name="Financeiro",
            timeout=15,
        )
        return True
    except Exception:
        return False


def enviar_notificacao_windows(titulo: str, mensagem: str) -> bool:
    """Exibe notificacao do sistema (Windows). Tenta toast nativo e depois fallback."""
    if sys.platform != "win32":
        return False

    titulo = (titulo or "").strip()
    mensagem = (mensagem or "").strip()
    if not titulo:
        return False

    if _enviar_via_powershell(titulo, mensagem):
        return True
    return _enviar_via_plyer(titulo, mensagem)


def enviar_notificacao_resumo_carteira(resumo: str) -> bool:
    """Toast com o resumo consolidado da carteira (uma unica mensagem visivel)."""
    texto = (resumo or "").strip()
    if not texto:
        return False

    texto = texto[:250]
    if len(texto) <= 120:
        return enviar_notificacao_windows(texto, "")

    return enviar_notificacao_windows(texto[:120], texto[120:])


def enviar_varias_notificacoes_windows(
    itens: list[tuple[str, str]],
    intervalo_segundos: float = 0.8,
) -> int:
    """Envia varias notificacoes com pequeno intervalo para nao sobrepor."""
    enviadas = 0
    for indice, (titulo, mensagem) in enumerate(itens):
        if indice > 0 and intervalo_segundos > 0:
            time.sleep(intervalo_segundos)
        if enviar_notificacao_windows(titulo, mensagem):
            enviadas += 1
    return enviadas
