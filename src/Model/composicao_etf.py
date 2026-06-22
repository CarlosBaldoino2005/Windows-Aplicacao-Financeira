"""Composicao da carteira de um ETF (ativos e pesos)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AtivoComposicaoEtf:
    """Um ativo presente na carteira do ETF."""

    simbolo: str
    nome: str
    percentual: float  # 0 a 100


@dataclass
class ComposicaoEtf:
    """Lista de posicoes reportadas para o ETF."""

    simbolo_etf: str
    nome_etf: str
    ativos: list[AtivoComposicaoEtf] = field(default_factory=list)
    fonte: str = "Yahoo Finance"
    aviso: str | None = None
    simbolo_consultado: str | None = None
