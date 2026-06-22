"""Favoritos do painel ETFs (arquivo separado)."""
from __future__ import annotations

from src.Service.favoritos_servico import FavoritosServico
from src.Tool.etfs_helper import eh_etf
from src.Tool.validadores import normalizar_simbolo


class FavoritosEtfsServico(FavoritosServico):
    """Persiste favoritos em dados/favoritos_etfs.json e valida se e ETF."""

    def __init__(self) -> None:
        super().__init__(
            nome_arquivo="favoritos_etfs.json",
            rotulo_ativo="ETF",
        )

    def adicionar(self, simbolo: str) -> tuple[bool, str | None]:
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            return False, erro
        if not eh_etf(simbolo_ok):
            codigo = simbolo_ok.replace(".SA", "")
            return (
                False,
                f"{codigo} nao consta como ETF nas fontes consultadas.",
            )
        return super().adicionar(simbolo_ok)
