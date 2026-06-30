"""Eixo intraday para pregão da Nasdaq (horario exibido nos candles)."""
from __future__ import annotations

import numpy as np
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter, NullLocator

from src.View.grafico_helper import minutos_dia_para_horario


def calcular_limites_eixo_nasdaq(
    posicoes_x: list[float] | np.ndarray,
    valores: list[float] | np.ndarray,
    *,
    preco_fechamento_anterior: float | None = None,
    projecao=None,
    margem_y_pct: float = 0.12,
    referencias_y_extra: list[float] | None = None,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Limites de X e Y com foco no intervalo dos dados (pregao US)."""
    xs = np.asarray(posicoes_x, dtype=float)
    ys = np.asarray(valores, dtype=float)

    referencias_y = list(ys.astype(float))
    if preco_fechamento_anterior is not None:
        referencias_y.append(float(preco_fechamento_anterior))
    if projecao is not None and getattr(projecao, "valores", None):
        referencias_y.extend(float(valor) for valor in projecao.valores)
    if referencias_y_extra:
        referencias_y.extend(float(valor) for valor in referencias_y_extra)

    y_min = float(min(referencias_y))
    y_max = float(max(referencias_y))
    span = max(y_max - y_min, max(y_max, 1.0) * 0.003, 0.05)
    pad = span * margem_y_pct
    ylim = (y_min - pad, y_max + pad)

    x_min_dados = float(xs.min())
    x_max_dados = float(xs.max())
    if projecao is not None and getattr(projecao, "posicoes_x", None):
        x_max_dados = max(x_max_dados, float(max(projecao.posicoes_x)))

    xlim_min = max(0.0, x_min_dados - 12.0)
    xlim_max = x_max_dados + 18.0
    if xlim_max <= xlim_min:
        xlim_max = xlim_min + 60.0

    return (xlim_min, xlim_max), ylim


def configurar_eixo_intraday_nasdaq(
    eixo,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> None:
    """Ticks de horario a cada 30 min no intervalo visivel."""
    eixo.set_xlim(xlim)
    eixo.set_ylim(ylim)

    passo = 30
    inicio = int(xlim[0] // passo) * passo
    fim = int(xlim[1])
    ticks = [pos for pos in range(inicio, fim + 1, passo) if xlim[0] <= pos <= xlim[1]]
    if len(ticks) < 2:
        ticks = [int(xlim[0]), int(xlim[1])]

    rotulos = [minutos_dia_para_horario(posicao) for posicao in ticks]
    eixo.xaxis.set_major_locator(FixedLocator(ticks))
    eixo.xaxis.set_major_formatter(FixedFormatter(rotulos))
    eixo.xaxis.set_minor_locator(NullLocator())
    eixo.xaxis.set_minor_formatter(NullFormatter())
    eixo.tick_params(axis="x", rotation=0, labelsize=9)
    for rotulo in eixo.get_xticklabels():
        rotulo.set_ha("center")
