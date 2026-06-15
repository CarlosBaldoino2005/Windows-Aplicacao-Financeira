"""Ponto de entrada para Agendador de Tarefas do Windows (app fechado)."""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def main() -> None:
    raiz = Path(__file__).resolve().parents[2]
    os.chdir(raiz)
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))
    os.environ.setdefault("PYTHONPATH", str(raiz))

    from src.Tool.registrador_log import RegistradorLog
    from src.Tool.relatorio_agendado_executor import executar_ciclo_relatorio_agendado

    log = RegistradorLog(raiz)
    try:
        resultado = executar_ciclo_relatorio_agendado(pasta_base=raiz)
        if resultado.executado:
            if resultado.mensagem:
                log.erro(f"Agendador: {resultado.mensagem}")
            else:
                nome_pdf = resultado.caminho_pdf.name if resultado.caminho_pdf else "PDF"
                log.info(f"Agendador: relatorio executado ({nome_pdf}).")
        elif resultado.mensagem:
            log.info(f"Agendador: {resultado.mensagem}")
    except Exception:
        log.erro(f"Agendador: falha inesperada.\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
