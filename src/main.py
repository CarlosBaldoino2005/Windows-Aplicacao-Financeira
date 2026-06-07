"""
Financeiro - aplicacao desktop 100% Python.
Execute: python -m src.main
Ou use: scripts\\desenvolver.ps1
"""
from pathlib import Path

from src.Tool.registrador_log import RegistradorLog
from src.Tool.registrar_toast_windows_helper import registrar_toast_windows
from src.View.interface_app import iniciar_interface

RAIZ = Path(__file__).resolve().parent.parent


def executar() -> None:
    log = RegistradorLog(RAIZ)
    log.info("Iniciando interface desktop Financeiro.")
    if registrar_toast_windows(RAIZ):
        log.info("Notificacoes Windows registradas (AppUserModelID).")
    else:
        log.aviso(
            "Notificacoes Windows: atalho nao registrado (instale pywin32). "
            "Sera usado fallback quando possivel."
        )
    iniciar_interface()


if __name__ == "__main__":
    executar()
