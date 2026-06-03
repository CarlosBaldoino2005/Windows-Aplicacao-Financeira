"""
Financeiro - aplicacao desktop 100% Python.
Execute: python -m src.main
Ou use: scripts\\desenvolver.ps1
"""
from pathlib import Path

from src.Tool.registrador_log import RegistradorLog
from src.View.interface_app import iniciar_interface

RAIZ = Path(__file__).resolve().parent.parent


def executar() -> None:
    log = RegistradorLog(RAIZ)
    log.info("Iniciando interface desktop Financeiro.")
    iniciar_interface()


if __name__ == "__main__":
    executar()
