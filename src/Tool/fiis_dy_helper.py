"""Calculo de Dividend Yield (DY) de FIIs em um periodo."""
from __future__ import annotations

from datetime import datetime, timedelta

from src.Tool.dividendos_helper import analisar_dividendos_periodo

_DIAS_POR_PERIODO: dict[str, int] = {
    "dia": 1,
    "semana": 7,
    "mes": 30,
    "trimestre": 92,
    "semestre": 183,
    "ano": 366,
    "tres_anos": 365 * 3,
    "cinco_anos": 365 * 5,
}


def resolver_intervalo_periodo(
    periodo_chave: str,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
) -> tuple[datetime, datetime] | None:
    """Converte chave de periodo (ou datas personalizadas) em intervalo fechado."""
    if periodo_chave == "personalizado":
        if data_inicio is None or data_fim is None:
            return None
        inicio = data_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        fim = data_fim.replace(hour=23, minute=59, second=59, microsecond=0)
        if inicio > fim:
            inicio, fim = fim, inicio
        return inicio, fim

    dias = _DIAS_POR_PERIODO.get(periodo_chave, 30)
    fim = datetime.now()
    inicio = (fim - timedelta(days=dias)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return inicio, fim


def calcular_dy_fii_no_periodo(
    simbolo: str,
    preco_atual: float,
    periodo_chave: str,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    moeda: str = "BRL",
) -> tuple[float, float] | None:
    """
    Retorna (dy_percentual, total_proventos_por_cota) no periodo.
    DY = proventos pagos no intervalo / preco atual da cota x 100.
    """
    if preco_atual <= 0:
        return None

    intervalo = resolver_intervalo_periodo(periodo_chave, data_inicio, data_fim)
    if intervalo is None:
        return None

    inicio, fim = intervalo
    analise = analisar_dividendos_periodo(
        simbolo,
        inicio.strftime("%d/%m/%Y"),
        fim.strftime("%d/%m/%Y"),
        moeda,
    )
    total_proventos = float(analise.get("total_dividendos_periodo") or 0.0)
    dy_pct = round((total_proventos / preco_atual) * 100, 2)
    return dy_pct, round(total_proventos, 4)
