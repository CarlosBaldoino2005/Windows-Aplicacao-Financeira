"""Favoritos do painel Fundos imobiliarios (arquivo separado)."""
from __future__ import annotations

from src.Service.favoritos_servico import FavoritosServico
from src.Tool.fiis_helper import eh_fii
from src.Tool.validadores import normalizar_simbolo


class FavoritosFiisServico(FavoritosServico):
    """Persiste favoritos em dados/favoritos_fiis.json e valida se e FII."""

    def __init__(self) -> None:
        super().__init__(
            nome_arquivo="favoritos_fiis.json",
            rotulo_ativo="fundo imobiliario",
        )

    def adicionar(self, simbolo: str) -> tuple[bool, str | None]:
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            return False, erro
        if not eh_fii(simbolo_ok):
            codigo = simbolo_ok.replace(".SA", "")
            return (
                False,
                f"{codigo} nao consta como fundo imobiliario (FII) nas fontes consultadas.",
            )
        return super().adicionar(simbolo_ok)
