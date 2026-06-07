"""Registra o Financeiro no Windows para exibir toasts (AppUserModelID + atalho)."""
from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

APP_ID_TOAST = "Carlos.Financeiro.Painel"
_NOME_ATALHO = "Financeiro.lnk"


def _definir_app_id_processo(app_id: str) -> None:
    """Informa ao Windows qual AppUserModelID usar para este processo."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        try:
            from win32com.shell import shell as shell_win32

            shell_win32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass


def _caminho_atalho_inicio() -> Path:
    return (
        Path(os.environ["APPDATA"])
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / _NOME_ATALHO
    )


def _criar_atalho_com_app_id(
    app_id: str,
    raiz_projeto: Path,
    executavel: str,
    argumentos: str,
) -> bool:
    """Cria atalho no Menu Iniciar com System.AppUserModel.ID (requer pywin32)."""
    try:
        import pythoncom
        from win32com.propsys import propsys, pscon
        from win32com.shell import shellcon
        import win32com.client
    except ImportError:
        return False

    caminho_atalho = _caminho_atalho_inicio()
    caminho_atalho.parent.mkdir(parents=True, exist_ok=True)

    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        atalho = shell.CreateShortcut(str(caminho_atalho))
        atalho.TargetPath = executavel
        atalho.Arguments = argumentos
        atalho.WorkingDirectory = str(raiz_projeto)
        atalho.Description = "Financeiro - Painel de Mercado"
        atalho.IconLocation = executavel
        atalho.save()

        store = propsys.SHGetPropertyStoreFromParsingName(
            str(caminho_atalho),
            None,
            shellcon.GPS_READWRITE,
            propsys.IID_IPropertyStore,
        )
        store.SetValue(
            pscon.PKEY_AppUserModel_ID,
            propsys.PROPVARIANTType(app_id, pythoncom.VT_LPWSTR),
        )
        store.Commit()
        return caminho_atalho.is_file()
    except Exception:
        return False


def registrar_toast_windows(raiz_projeto: Path | None = None) -> bool:
    """
    Prepara toasts nativos do Windows para o app desktop.
    Deve ser chamado no inicio, antes de exibir a interface.
    """
    if sys.platform != "win32":
        return False

    raiz = raiz_projeto or Path(__file__).resolve().parents[2]
    _definir_app_id_processo(APP_ID_TOAST)

    argumentos = "-m src.main"
    return _criar_atalho_com_app_id(
        APP_ID_TOAST,
        raiz,
        sys.executable,
        argumentos,
    )
