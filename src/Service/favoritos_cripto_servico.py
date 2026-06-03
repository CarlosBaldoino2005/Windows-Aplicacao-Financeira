"""Persistencia da lista de criptomoedas favoritas."""
from __future__ import annotations

from pathlib import Path

from src.Service.favoritos_servico import FavoritosServico
from src.Tool.validadores import normalizar_simbolo_cripto

_ARQUIVO_CRIPTO = "favoritos_cripto.json"


class FavoritosCriptoServico(FavoritosServico):
    """Favoritos em dados/favoritos_cripto.json."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        super().__init__(
            pasta_base,
            nome_arquivo=_ARQUIVO_CRIPTO,
            fn_normalizar=normalizar_simbolo_cripto,
            rotulo_ativo="criptomoeda",
        )
