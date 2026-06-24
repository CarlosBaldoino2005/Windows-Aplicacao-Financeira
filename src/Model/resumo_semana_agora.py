"""Metricas diarias dos ultimos pregões para a tela Resumo do mês (Agora)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DiaResumoSemanaAgora:
    """Um dia de pregão com OHLCV e variacao em relacao ao fechamento anterior."""

    data: date
    abertura: float
    maxima: float
    minima: float
    fechamento: float
    variacao_valor: float
    variacao_pct: float
    amplitude_valor: float
    amplitude_pct: float
    fechamento_anterior: float | None
    volume: int | None
    horario_alta: str = "—"
    horario_baixa: str = "—"


@dataclass(frozen=True)
class ResumoSemanaAgora:
    """Consolidado dos ultimos trinta dias uteis do ativo."""

    simbolo: str
    nome: str
    moeda: str
    dias: tuple[DiaResumoSemanaAgora, ...]
    variacao_acumulada_valor: float | None
    variacao_acumulada_pct: float | None
    media_fechamento: float | None
    volume_total: int | None
    aviso: str = ""
