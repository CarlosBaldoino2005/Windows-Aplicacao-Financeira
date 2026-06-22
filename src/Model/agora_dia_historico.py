"""Resumo intraday de um dia historico na tela Agora."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ResumoDiaAgora:
    data: date
    simbolo: str
    nome: str
    moeda: str
    abertura: float
    fechamento: float
    maxima: float
    minima: float
    variacao_valor: float
    variacao_pct: float
    fechamento_anterior: float | None
    volume_total: int | None = None
