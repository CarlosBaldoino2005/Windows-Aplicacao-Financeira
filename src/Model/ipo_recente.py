"""Modelo de linha para IPOs recentes (Brasil e mundo)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

TipoAtivoIpo = Literal["acoes", "cripto", "etfs"]


@dataclass
class LinhaIpoRecente:
    """Dados de um IPO listado nos ultimos 30 dias."""

    simbolo: str
    nome: str
    mercado: str
    na_b3: bool
    simbolo_b3: str | None
    data_ipo: date
    abriu_hoje: bool
    preco_abertura_capital: float | None
    preco_atual: float | None
    variacao_desde_ipo_pct: float | None
    variacao_desde_ipo_valor: float | None
    preco_baixa_dia: float | None
    hora_baixa_dia: str | None
    variacao_baixa_dia_pct: float | None
    preco_alta_dia: float | None
    hora_alta_dia: str | None
    variacao_alta_dia_pct: float | None
    preco_fechamento_dia: float | None
    moeda: str = "USD"
    tipo_ativo: TipoAtivoIpo = "acoes"
