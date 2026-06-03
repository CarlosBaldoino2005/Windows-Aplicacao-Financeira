"""Cores e fontes do modelo-ui aplicadas na interface Python."""
import json
from pathlib import Path


def carregar_tema() -> dict:
    caminho = Path(__file__).resolve().parents[2] / "modelo-ui" / "design-tokens.json"
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    return dados["cores"]


CORES = carregar_tema()
