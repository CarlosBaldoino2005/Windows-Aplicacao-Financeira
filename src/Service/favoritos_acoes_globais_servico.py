"""Favoritos do painel de acoes globais (BDRs na B3)."""
from __future__ import annotations

from src.Service.favoritos_servico import FavoritosServico
from src.Tool.bdrs_helper import eh_bdr_b3
from src.Tool.validadores import normalizar_simbolo


class FavoritosAcoesGlobaisServico(FavoritosServico):
    """Persiste favoritos em dados/favoritos_acoes_globais.json."""

    def __init__(self) -> None:
        super().__init__(
            nome_arquivo="favoritos_acoes_globais.json",
            rotulo_ativo="BDR",
        )

    def adicionar(self, simbolo: str) -> tuple[bool, str | None]:
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            return False, erro
        if not eh_bdr_b3(simbolo_ok):
            codigo = simbolo_ok.replace(".SA", "")
            return (
                False,
                f"{codigo} nao consta como BDR negociado na B3.",
            )
        return super().adicionar(simbolo_ok)
