"""Projecao linear do preco ate o fechamento do pregao na tela Agora."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.View.grafico_helper import HORA_FIM_PREGAO_AGORA, HORA_INICIO_PREGAO_AGORA

_PASSO_MINUTOS_PADRAO = 5
_MINIMO_PONTOS = 2


@dataclass(frozen=True)
class ProjecaoFimDiaAgora:
    """Serie projetada do ultimo preco real ate o fim do pregao."""

    posicoes_x: list[float]
    valores: list[float]
    preco_fechamento_projetado: float
    inclinacao_por_minuto: float


def calcular_projecao_fim_dia(
    posicoes_x: list[float] | np.ndarray,
    valores: list[float] | np.ndarray,
    *,
    passo_minutos: int = _PASSO_MINUTOS_PADRAO,
    hora_inicio: int = HORA_INICIO_PREGAO_AGORA,
    hora_fim: int = HORA_FIM_PREGAO_AGORA,
) -> ProjecaoFimDiaAgora | None:
    """
    Estima o restante do dia com regressao linear sobre o intraday.

    A inclinacao e calculada sobre todos os pontos disponiveis e a curva
    projetada ancora no ultimo preco real (atualizado a cada refresh).
    """
    if len(posicoes_x) < _MINIMO_PONTOS or len(valores) < _MINIMO_PONTOS:
        return None

    xs = np.asarray(posicoes_x, dtype=float)
    ys = np.asarray(valores, dtype=float)
    if xs.size != ys.size or xs.size < _MINIMO_PONTOS:
        return None

    inicio_pregao = hora_inicio * 60
    fim_pregao = hora_fim * 60
    x_atual = float(xs[-1])
    y_atual = float(ys[-1])

    if x_atual >= fim_pregao - 1:
        return None

    # Pontos dentro do pregao para a tendencia; ancora no ultimo preco real.
    mascara = (xs >= inicio_pregao) & (xs <= fim_pregao)
    xs_trend = xs[mascara] if mascara.sum() >= _MINIMO_PONTOS else xs
    ys_trend = ys[mascara] if mascara.sum() >= _MINIMO_PONTOS else ys

    if xs_trend.size >= 3:
        inclinacao = float(np.polyfit(xs_trend, ys_trend, 1)[0])
    else:
        delta_x = float(xs_trend[-1] - xs_trend[0])
        if abs(delta_x) < 1e-6:
            inclinacao = 0.0
        else:
            inclinacao = float((ys_trend[-1] - ys_trend[0]) / delta_x)

    passo = max(1, int(passo_minutos))
    posicoes_proj: list[float] = [x_atual]
    valores_proj: list[float] = [y_atual]

    proximo = int(x_atual) + passo
    while proximo < fim_pregao:
        posicoes_proj.append(float(proximo))
        valores_proj.append(_preco_projetado(y_atual, x_atual, inclinacao, float(proximo)))
        proximo += passo

    if posicoes_proj[-1] != float(fim_pregao):
        posicoes_proj.append(float(fim_pregao))
        valores_proj.append(_preco_projetado(y_atual, x_atual, inclinacao, float(fim_pregao)))
    else:
        valores_proj[-1] = _preco_projetado(y_atual, x_atual, inclinacao, float(fim_pregao))

    preco_fechamento = round(valores_proj[-1], 2)
    if preco_fechamento <= 0:
        return None

    return ProjecaoFimDiaAgora(
        posicoes_x=posicoes_proj,
        valores=[round(valor, 2) for valor in valores_proj],
        preco_fechamento_projetado=preco_fechamento,
        inclinacao_por_minuto=round(inclinacao, 6),
    )


def _preco_projetado(y_atual: float, x_atual: float, inclinacao: float, x_destino: float) -> float:
    return round(y_atual + inclinacao * (x_destino - x_atual), 2)
