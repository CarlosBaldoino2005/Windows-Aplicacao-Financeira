"""Toast nativo do Windows 10+ para alertas do monitoramento."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

from src.Tool.registrar_toast_windows_helper import APP_ID_TOAST

_SCRIPT_TOAST = r"""
param(
    [Parameter(Mandatory = $true)][string]$Titulo,
    [Parameter(Mandatory = $true)][string]$Mensagem,
    [Parameter(Mandatory = $true)][string]$AppId
)
try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
        [Windows.UI.Notifications.ToastTemplateType]::ToastText02
    )
    $raw = [xml]$template.GetXml()
    ($raw.toast.visual.binding.text | Where-Object { $_.id -eq "1" }).AppendChild($raw.CreateTextNode($Titulo)) | Out-Null
    ($raw.toast.visual.binding.text | Where-Object { $_.id -eq "2" }).AppendChild($raw.CreateTextNode($Mensagem)) | Out-Null
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
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".ps1",
            delete=False,
            encoding="utf-8",
        ) as arquivo:
            arquivo.write(_SCRIPT_TOAST)
            caminho_script = Path(arquivo.name)

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
                "-Titulo",
                titulo,
                "-Mensagem",
                mensagem,
                "-AppId",
                APP_ID_TOAST,
            ],
            timeout=15,
            creationflags=flags,
            check=False,
            capture_output=True,
            text=True,
        )
        return resultado.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
    finally:
        if caminho_script is not None:
            try:
                caminho_script.unlink(missing_ok=True)
            except OSError:
                pass


def _enviar_via_plyer(titulo: str, mensagem: str) -> bool:
    """Fallback: balao na bandeja do sistema (nao exige AppUserModelID)."""
    try:
        from plyer import notification

        notification.notify(
            title=titulo,
            message=mensagem,
            app_name="Financeiro",
            timeout=12,
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
