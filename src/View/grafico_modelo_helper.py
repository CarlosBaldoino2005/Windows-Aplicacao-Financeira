"""Tipos de visualizacao do grafico de precos (linha, area, vela, barra)."""
from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import customtkinter as ctk
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

ModeloGrafico = Literal["linha", "area", "vela", "barra"]

MODELOS_GRAFICO: tuple[tuple[ModeloGrafico, str], ...] = (
    ("linha", "Linha"),
    ("area", "Area"),
    ("vela", "Vela"),
    ("barra", "Barra"),
)

_MODELO_PADRAO: ModeloGrafico = "linha"
_COR_ALTA = "#16A34A"
_COR_BAIXA = "#DC2626"


def rotulos_modelo_grafico() -> list[str]:
    """Rotulos exibidos no seletor de modelo."""
    return [rotulo for _, rotulo in MODELOS_GRAFICO]


def chave_por_rotulo_modelo(rotulo: str) -> ModeloGrafico:
    """Converte rotulo da combo para chave interna."""
    texto = (rotulo or "").strip().lower()
    for chave, nome in MODELOS_GRAFICO:
        if nome.lower() == texto:
            return chave
    return _MODELO_PADRAO


def rotulo_por_chave_modelo(chave: str | None) -> str:
    """Converte chave interna para rotulo da combo."""
    texto = (chave or "").strip().lower()
    for chave_item, nome in MODELOS_GRAFICO:
        if chave_item == texto:
            return nome
    return MODELOS_GRAFICO[0][1]


def normalizar_modelo_grafico(valor: str | None) -> ModeloGrafico:
    """Valida modelo informado."""
    return chave_por_rotulo_modelo(rotulo_por_chave_modelo(valor))


def montar_seletor_modelo_grafico(
    pai: ctk.CTkFrame,
    *,
    modelo_inicial: str = _MODELO_PADRAO,
    ao_mudar: Callable[[ModeloGrafico], None],
    largura_combo: int = 120,
) -> ctk.CTkComboBox:
    """Cria rotulo + combo para escolher o modelo do grafico."""
    ctk.CTkLabel(pai, text="Modelo").pack(side="left", padx=(0, 8))
    combo = ctk.CTkComboBox(
        pai,
        values=rotulos_modelo_grafico(),
        width=largura_combo,
        command=lambda rotulo: ao_mudar(chave_por_rotulo_modelo(rotulo)),
    )
    combo.set(rotulo_por_chave_modelo(modelo_inicial))
    combo.pack(side="left", padx=(0, 16))
    return combo


def _linha_guia_interacao(
    eixo,
    indices: np.ndarray,
    valores: list[float],
    *,
    label: str | None = None,
) -> Line2D:
    """Linha transparente nos fechamentos para tooltip e selecao de periodo."""
    linha, = eixo.plot(
        indices,
        valores,
        color=CORES_TRANSPARENTE(),
        linewidth=0.8,
        marker="o",
        markersize=4,
        alpha=0.01,
        label=label or "_nolegend_",
        zorder=6,
    )
    return linha


def CORES_TRANSPARENTE() -> str:
    return "#00000000"


def _montar_pontos_vela_comparacao(serie: list[dict]) -> list[dict]:
    """Monta abertura/fechamento a partir do indice relativo para candlesticks."""
    pontos: list[dict] = []
    indice_anterior: float | None = None
    for ponto in serie:
        fechamento = float(ponto.get("indice_relativo") or 0)
        abertura = float(indice_anterior if indice_anterior is not None else fechamento)
        pontos.append({**ponto, "fechamento": fechamento, "abertura": abertura})
        indice_anterior = fechamento
    return pontos


def desenhar_series_comparacao(
    eixo,
    indices: np.ndarray,
    simbolos: list[str],
    series: dict[str, list[dict]],
    cores: list[str],
    *,
    modelo: ModeloGrafico | str = "linha",
    largura_barra: float = 0.65,
) -> list[Line2D]:
    """
    Desenha varias series de comparacao (indice base 100) no modelo escolhido.
    Retorna linhas guia para tooltip e selecao de periodo.
    """
    modelo_ok = normalizar_modelo_grafico(str(modelo))
    linhas_plot: list[Line2D] = []
    series_validas: list[tuple[str, list[dict]]] = []

    for simbolo in simbolos:
        serie = series.get(simbolo) or []
        if len(serie) >= 2:
            series_validas.append((simbolo, serie))

    quantidade = len(series_validas)
    largura_grupo = 0.75

    for indice_serie, (simbolo, serie) in enumerate(series_validas):
        cor = cores[indice_serie % len(cores)]
        valores = [float(p["indice_relativo"]) for p in serie]
        valores_np = np.asarray(valores, dtype=float)
        rotulo = simbolo.replace(".SA", "")

        if modelo_ok == "barra":
            if quantidade <= 1:
                posicoes_x = indices
                largura = largura_barra
            else:
                largura = largura_grupo / quantidade
                posicoes_x = indices + (indice_serie - (quantidade - 1) / 2) * largura
            eixo.bar(
                posicoes_x,
                valores_np,
                width=largura,
                color=cor,
                alpha=0.82,
                label=rotulo,
                zorder=2,
            )
        elif modelo_ok == "area":
            eixo.fill_between(indices, valores_np, alpha=0.18, color=cor, zorder=1)
            eixo.plot(
                indices,
                valores_np,
                color=cor,
                linewidth=2.2,
                marker="o",
                markersize=3,
                label=rotulo,
                zorder=3,
            )
        elif modelo_ok == "vela":
            pontos_vela = _montar_pontos_vela_comparacao(serie)
            if quantidade <= 1:
                posicoes_x = indices
                largura_corpo = largura_barra
            else:
                largura = largura_grupo / quantidade
                posicoes_x = indices + (indice_serie - (quantidade - 1) / 2) * largura
                largura_corpo = min(0.55, largura * 0.9)
            _desenhar_velas(eixo, posicoes_x, pontos_vela, largura_corpo)
        else:
            eixo.plot(
                indices,
                valores_np,
                label=rotulo,
                color=cor,
                linewidth=2.2,
                marker="o",
                markersize=3,
                zorder=3,
            )

        linhas_plot.append(
            _linha_guia_interacao(eixo, indices, valores, label=rotulo)
        )

    return linhas_plot


def desenhar_serie_preco_principal(
    eixo,
    indices: np.ndarray,
    valores: list[float],
    pontos_tooltip: list[dict],
    *,
    modelo: ModeloGrafico | str = "linha",
    cor: str,
    label: str = "Acao (fechamento)",
    largura_barra: float = 0.65,
) -> Line2D:
    """
    Desenha a serie principal conforme o modelo escolhido.
    Retorna linha guia nos precos de fechamento para tooltip e clique.
    """
    modelo_ok = normalizar_modelo_grafico(str(modelo))
    valores_np = np.asarray(valores, dtype=float)

    if modelo_ok == "barra":
        eixo.bar(
            indices,
            valores_np,
            width=largura_barra,
            color=cor,
            alpha=0.82,
            label=label,
            zorder=2,
        )
    elif modelo_ok == "area":
        eixo.fill_between(indices, valores_np, alpha=0.22, color=cor, zorder=1)
        eixo.plot(
            indices,
            valores_np,
            color=cor,
            linewidth=2,
            marker="o",
            markersize=3,
            label=label,
            zorder=3,
        )
    elif modelo_ok == "vela":
        _desenhar_velas(eixo, indices, pontos_tooltip, largura_barra)
        return _linha_guia_interacao(eixo, indices, valores, label=label)
    else:
        eixo.plot(
            indices,
            valores_np,
            color=cor,
            linewidth=2,
            marker="o",
            markersize=3,
            label=label,
            zorder=3,
        )

    return _linha_guia_interacao(eixo, indices, valores)


def _desenhar_velas(
    eixo,
    indices: np.ndarray,
    pontos_tooltip: list[dict],
    largura_corpo: float,
) -> None:
    """Desenha candlesticks simplificados com abertura e fechamento."""
    for indice, ponto in zip(indices, pontos_tooltip, strict=False):
        fechamento = float(ponto.get("fechamento") or 0)
        abertura_raw = ponto.get("abertura")
        abertura = float(abertura_raw) if abertura_raw is not None else fechamento
        topo = max(abertura, fechamento)
        base = min(abertura, fechamento)
        cor = _COR_ALTA if fechamento >= abertura else _COR_BAIXA

        eixo.plot(
            [indice, indice],
            [base, topo],
            color=cor,
            linewidth=1.2,
            solid_capstyle="round",
            zorder=2,
        )

        altura = topo - base
        if altura <= 0:
            altura = max(abs(topo) * 0.0005, 0.01)

        corpo = Rectangle(
            (float(indice) - largura_corpo / 2, base),
            largura_corpo,
            altura,
            facecolor=cor,
            edgecolor=cor,
            linewidth=0.8,
            zorder=3,
        )
        eixo.add_patch(corpo)
