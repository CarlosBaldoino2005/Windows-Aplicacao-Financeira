"""Calculo de dias uteis para interfaces financeiras (B3)."""
from __future__ import annotations

from datetime import date, timedelta


def calcular_ultimo_dia_util(referencia: date | None = None) -> date:
    """Retorna o ultimo dia util anterior a referencia (ignora sabado e domingo)."""
    atual = referencia or date.today()
    candidato = atual - timedelta(days=1)
    while candidato.weekday() >= 5:
        candidato -= timedelta(days=1)
    return candidato


def eh_dia_util(valor: date) -> bool:
    return valor.weekday() < 5


def formatar_data_ptbr(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")
