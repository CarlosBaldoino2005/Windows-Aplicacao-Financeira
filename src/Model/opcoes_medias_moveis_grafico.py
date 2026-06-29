"""Opcoes de medias moveis (MM e MME) nos graficos de preco."""
from __future__ import annotations

from dataclasses import dataclass

PERIODO_MM_PADRAO = 20
PERIODO_MME_PADRAO = 9


@dataclass(frozen=True)
class OpcoesMediasMoveisGrafico:
    """Periodos e exibicao das medias sobre o fechamento."""

    mm_ativa: bool = False
    mm_periodo: int = PERIODO_MM_PADRAO
    mme_ativa: bool = False
    mme_periodo: int = PERIODO_MME_PADRAO

    def alguma_ativa(self) -> bool:
        return self.mm_ativa or self.mme_ativa
