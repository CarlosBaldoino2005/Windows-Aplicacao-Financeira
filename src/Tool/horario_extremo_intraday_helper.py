"""Horarios em que o ativo atingiu a maxima e a minima do dia (intraday)."""
from __future__ import annotations

from src.Model.cotacao import PontoHistorico
from src.View.grafico_helper import extrair_minutos_dia_de_ponto, minutos_dia_para_horario

_TOLERANCIA_PRECO = 0.02
_HORARIO_INDISPONIVEL = "—"


def horario_para_minutos_ordenacao(texto: str) -> int:
    """Converte HH:MM em minutos para ordenacao da grid; vazio/— fica no fim."""
    limpo = (texto or "").strip()
    if not limpo or limpo == _HORARIO_INDISPONIVEL:
        return -1
    partes = limpo.split(":")
    if len(partes) != 2:
        return -1
    try:
        hora = int(partes[0])
        minuto = int(partes[1])
    except ValueError:
        return -1
    if hora < 0 or hora > 23 or minuto < 0 or minuto > 59:
        return -1
    return hora * 60 + minuto


def obter_horarios_alta_baixa_intraday(
    pontos: list[PontoHistorico],
    *,
    preco_alta: float,
    preco_baixa: float,
) -> tuple[str, str]:
    """Retorna horarios (HH:MM) da primeira ocorrencia da alta e da baixa do dia."""
    if not pontos:
        return _HORARIO_INDISPONIVEL, _HORARIO_INDISPONIVEL

    hora_alta = ""
    hora_baixa = ""

    for ponto in pontos:
        horario = _horario_do_ponto(ponto)
        if not horario:
            continue
        for preco in _precos_do_ponto(ponto):
            if not hora_alta and abs(preco - preco_alta) <= _TOLERANCIA_PRECO:
                hora_alta = horario
            if not hora_baixa and abs(preco - preco_baixa) <= _TOLERANCIA_PRECO:
                hora_baixa = horario
        if hora_alta and hora_baixa:
            break

    if not hora_alta or not hora_baixa:
        alta_serie, baixa_serie = _horarios_extremos_da_serie(pontos)
        if not hora_alta:
            hora_alta = alta_serie
        if not hora_baixa:
            hora_baixa = baixa_serie

    return (
        hora_alta or _HORARIO_INDISPONIVEL,
        hora_baixa or _HORARIO_INDISPONIVEL,
    )


def _horario_do_ponto(ponto: PontoHistorico) -> str | None:
    minutos = extrair_minutos_dia_de_ponto(ponto.data_exibicao, data_iso=ponto.data_iso)
    if minutos is None:
        return None
    return minutos_dia_para_horario(minutos)


def _precos_do_ponto(ponto: PontoHistorico) -> list[float]:
    valores: list[float] = []
    for bruto in (ponto.preco_fechamento, ponto.preco_abertura):
        if bruto is None:
            continue
        try:
            preco = float(bruto)
        except (TypeError, ValueError):
            continue
        if preco > 0:
            valores.append(preco)
    return valores


def _horarios_extremos_da_serie(pontos: list[PontoHistorico]) -> tuple[str, str]:
    preco_maximo: float | None = None
    preco_minimo: float | None = None
    horario_maximo = ""
    horario_minimo = ""

    for ponto in pontos:
        horario = _horario_do_ponto(ponto)
        if not horario:
            continue
        for preco in _precos_do_ponto(ponto):
            if preco_maximo is None or preco > preco_maximo:
                preco_maximo = preco
                horario_maximo = horario
            if preco_minimo is None or preco < preco_minimo:
                preco_minimo = preco
                horario_minimo = horario

    return horario_maximo, horario_minimo
