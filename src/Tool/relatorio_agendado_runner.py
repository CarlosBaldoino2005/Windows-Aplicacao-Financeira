"""Ponto de entrada para Agendador de Tarefas do Windows (app fechado)."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    raiz = Path(__file__).resolve().parents[2]
    os.chdir(raiz)
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))
    os.environ.setdefault("PYTHONPATH", str(raiz))

    from src.Tool.relatorio_agendado_executor import executar_ciclo_relatorio_agendado

    executar_ciclo_relatorio_agendado(pasta_base=raiz)


if __name__ == "__main__":
    main()
