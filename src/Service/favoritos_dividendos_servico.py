"""Favoritos do painel Empresa + dividendos (arquivo separado)."""
from __future__ import annotations

from src.Service.favoritos_servico import FavoritosServico
from src.Tool.dividendos_helper import eh_pagadora_dividendos
from src.Tool.validadores import normalizar_simbolo


class FavoritosDividendosServico(FavoritosServico):
    """Persiste favoritos em dados/favoritos_dividendos.json e valida pagamento de dividendos."""

    def __init__(self) -> None:
        super().__init__(
            nome_arquivo="favoritos_dividendos.json",
            rotulo_ativo="empresa com dividendos",
        )

    def adicionar(self, simbolo: str) -> tuple[bool, str | None]:
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            return False, erro
        if not eh_pagadora_dividendos(simbolo_ok):
            codigo = simbolo_ok.replace(".SA", "")
            return (
                False,
                f"{codigo} nao consta como pagadora de dividendos nas fontes consultadas.",
            )
        return super().adicionar(simbolo_ok)
