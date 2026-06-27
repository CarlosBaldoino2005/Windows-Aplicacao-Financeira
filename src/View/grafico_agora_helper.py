"""Grafico intraday da tela Agora no estilo Google Finance."""
from __future__ import annotations

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter, NullLocator

from src.View.formatadores import formatar_moeda
from src.View.grafico_helper import (
    ALPHA_AREA_GRAFICO,
    HORA_FIM_PREGAO_AGORA,
    HORA_INICIO_PREGAO_AGORA,
    INTERVALO_TICKS_HORARIO_AGORA,
    LARGURA_LINHA_GRAFICO,
    MARGEM_GRAFICO_BOTTOM,
    MARGEM_GRAFICO_LEFT,
    MARGEM_GRAFICO_RIGHT,
    MARGEM_GRAFICO_TOP,
    aplicar_grade_padrao_grafico,
    aplicar_tema_matplotlib,
    aplicar_titulo_padrao_grafico,
    minutos_dia_para_horario,
)
from src.View.grafico_modelo_helper import ModeloGrafico, _marcar_ultimo_ponto_serie, desenhar_serie_preco_principal
from src.Tool.projecao_intraday_agora_helper import ProjecaoFimDiaAgora
from src.View.tema import CORES

_COR_ALTA_GOOGLE = "#34A853"
_COR_BAIXA_GOOGLE = "#EA4335"
_LARGURA_LINHA_PROJECAO = 1.8


def calcular_preco_fechamento_anterior(preco: float | None, variacao_valor: float | None) -> float | None:
    """Deriva o fechamento do dia anterior a partir da cotacao atual."""
    if preco is None or variacao_valor is None:
        return None
    anterior = round(float(preco) - float(variacao_valor), 2)
    return anterior if anterior > 0 else None


def obter_cor_tendencia_agora(
    preco_atual: float | None,
    preco_fechamento_anterior: float | None,
) -> str:
    """Verde se acima do fechamento anterior; vermelho caso contrario."""
    if preco_atual is None or preco_fechamento_anterior is None:
        return CORES.get("sucesso", _COR_ALTA_GOOGLE)
    if float(preco_atual) >= float(preco_fechamento_anterior):
        return CORES.get("sucesso", _COR_ALTA_GOOGLE)
    return CORES.get("erro", _COR_BAIXA_GOOGLE)


def calcular_limites_eixo_agora(
    posicoes_x: list[float] | np.ndarray,
    valores: list[float] | np.ndarray,
    *,
    preco_fechamento_anterior: float | None = None,
    projecao: ProjecaoFimDiaAgora | None = None,
    margem_y_pct: float = 0.12,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Limites de X e Y com zoom no preco (sem iniciar em zero)."""
    xs = np.asarray(posicoes_x, dtype=float)
    ys = np.asarray(valores, dtype=float)

    referencias_y = list(ys.astype(float))
    if preco_fechamento_anterior is not None:
        referencias_y.append(float(preco_fechamento_anterior))
    if projecao is not None and projecao.valores:
        referencias_y.extend(float(valor) for valor in projecao.valores)

    y_min = float(min(referencias_y))
    y_max = float(max(referencias_y))
    span = max(y_max - y_min, max(y_max, 1.0) * 0.003, 0.05)
    pad = span * margem_y_pct
    ylim = (y_min - pad, y_max + pad)

    x_min_dados = float(xs.min())
    x_max_dados = float(xs.max())
    if projecao is not None and projecao.posicoes_x:
        x_max_dados = max(x_max_dados, float(max(projecao.posicoes_x)))
    inicio_pregao = HORA_INICIO_PREGAO_AGORA * 60
    fim_pregao = HORA_FIM_PREGAO_AGORA * 60

    xlim_min = max(inicio_pregao, x_min_dados - 12)
    xlim_max = min(fim_pregao, x_max_dados + 18)
    if xlim_max <= xlim_min:
        xlim_max = xlim_min + 60

    return (xlim_min, xlim_max), ylim


def configurar_eixo_intraday_agora(
    eixo,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> None:
    """Eixo X apenas no intervalo dos dados; grade horizontal suave."""
    eixo.set_xlim(xlim)
    eixo.set_ylim(ylim)

    passo = max(1, INTERVALO_TICKS_HORARIO_AGORA) * 60
    inicio = HORA_INICIO_PREGAO_AGORA * 60
    fim = HORA_FIM_PREGAO_AGORA * 60
    ticks = [pos for pos in range(inicio, fim + 1, passo) if xlim[0] <= pos <= xlim[1]]
    if not ticks:
        ticks = [int(xlim[0]), int(xlim[1])]

    rotulos = [minutos_dia_para_horario(posicao) for posicao in ticks]
    eixo.xaxis.set_major_locator(FixedLocator(ticks))
    eixo.xaxis.set_major_formatter(FixedFormatter(rotulos))
    eixo.xaxis.set_minor_locator(NullLocator())
    eixo.xaxis.set_minor_formatter(NullFormatter())
    eixo.tick_params(axis="x", rotation=0, labelsize=9)
    for rotulo in eixo.get_xticklabels():
        rotulo.set_ha("center")


def desenhar_linha_fechamento_anterior(
    eixo,
    preco_fechamento_anterior: float | None,
    moeda: str,
    xlim: tuple[float, float],
) -> None:
    """Linha pontilhada do fechamento anterior com rotulo a direita."""
    if preco_fechamento_anterior is None:
        return

    cor = CORES.get("textoSecundario", "#94A3B8")
    eixo.axhline(
        preco_fechamento_anterior,
        color=cor,
        linestyle=(0, (4, 4)),
        linewidth=1.0,
        alpha=0.85,
        zorder=2,
    )
    texto = f"Fech. ant. {formatar_moeda(preco_fechamento_anterior, moeda)}"
    eixo.text(
        xlim[1],
        preco_fechamento_anterior,
        f"  {texto}",
        va="center",
        ha="left",
        fontsize=8,
        color=cor,
        clip_on=False,
        zorder=5,
    )


def marcar_ultimo_ponto_agora(
    eixo,
    indices: np.ndarray,
    valores: np.ndarray,
    cor: str,
) -> None:
    """Circulo no ultimo preco, como no Google Finance."""
    _marcar_ultimo_ponto_serie(eixo, indices, valores, cor)


def obter_cor_projecao_agora() -> str:
    """Cor distinta da serie real (verde/vermelho) para a projecao."""
    return CORES.get("aviso", "#D97706")


def desenhar_projecao_fim_dia_agora(
    eixo,
    projecao: ProjecaoFimDiaAgora,
    moeda: str,
    xlim: tuple[float, float],
) -> None:
    """Linha tracejada do preco atual ate o fechamento projetado."""
    if not projecao.posicoes_x or len(projecao.posicoes_x) < 2:
        return

    cor = obter_cor_projecao_agora()
    posicoes = np.asarray(projecao.posicoes_x, dtype=float)
    valores = np.asarray(projecao.valores, dtype=float)

    eixo.plot(
        posicoes,
        valores,
        color=cor,
        linewidth=_LARGURA_LINHA_PROJECAO,
        linestyle=(0, (6, 4)),
        alpha=0.92,
        zorder=2,
        label="Projecao fechamento",
    )

    preco_fim = projecao.preco_fechamento_projetado
    eixo.scatter(
        [posicoes[-1]],
        [valores[-1]],
        s=36,
        color=cor,
        edgecolors=CORES.get("superficie", "#FFFFFF"),
        linewidths=1.2,
        zorder=4,
    )
    texto = f"Proj. {formatar_moeda(preco_fim, moeda)}"
    eixo.text(
        xlim[1],
        preco_fim,
        f"  {texto}",
        va="center",
        ha="left",
        fontsize=8,
        color=cor,
        clip_on=False,
        zorder=5,
    )


_PROPORCAO_PRECO_VOLUME = (4, 1)
_LARGURA_BARRA_VOLUME = 1.4


def formatar_volume_agora(volume: int | None) -> str:
    """Formata volume inteiro no padrao pt-BR (ex.: 24.224)."""
    if volume is None:
        return "—"
    return f"{int(volume):,}".replace(",", ".")


def criar_subplots_agora(figura):
    """Cria eixo de preco (topo) e volume (base) com eixo X compartilhado."""
    from matplotlib.gridspec import GridSpec

    grade = GridSpec(
        2,
        1,
        figure=figura,
        height_ratios=list(_PROPORCAO_PRECO_VOLUME),
        hspace=0.04,
    )
    eixo_preco = figura.add_subplot(grade[0])
    eixo_volume = figura.add_subplot(grade[1], sharex=eixo_preco)
    return eixo_preco, eixo_volume


def ocultar_rotulos_eixo_x_preco(eixo) -> None:
    """Esconde horarios no painel de preco quando o volume exibe o eixo X."""
    eixo.tick_params(axis="x", labelbottom=False)
    eixo.xaxis.set_minor_locator(NullLocator())
    eixo.xaxis.set_minor_formatter(NullFormatter())


def obter_cor_barra_volume(ponto: dict) -> str:
    """Verde se fechamento >= abertura; vermelho caso contrario."""
    fechamento = float(ponto.get("fechamento") or 0)
    abertura_raw = ponto.get("abertura")
    abertura = float(abertura_raw) if abertura_raw is not None else fechamento
    if fechamento >= abertura:
        return CORES.get("sucesso", _COR_ALTA_GOOGLE)
    return CORES.get("erro", _COR_BAIXA_GOOGLE)


def calcular_limites_eixo_volume(pontos_tooltip: list[dict]) -> tuple[float, float]:
    """Limites Y do painel de volume (sempre a partir de zero)."""
    volumes = [int(p["volume"]) for p in pontos_tooltip if p.get("volume")]
    if not volumes:
        return (0.0, 1.0)
    maximo = float(max(volumes))
    return (0.0, max(maximo * 1.08, 1.0))


def configurar_eixo_volume_agora(
    eixo,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> None:
    """Eixo X alinhado ao preco; ticks de horario apenas no painel inferior."""
    eixo.set_xlim(xlim)
    eixo.set_ylim(ylim)

    passo = max(1, INTERVALO_TICKS_HORARIO_AGORA) * 60
    inicio = HORA_INICIO_PREGAO_AGORA * 60
    fim = HORA_FIM_PREGAO_AGORA * 60
    ticks = [pos for pos in range(inicio, fim + 1, passo) if xlim[0] <= pos <= xlim[1]]
    if not ticks:
        ticks = [int(xlim[0]), int(xlim[1])]

    rotulos = [minutos_dia_para_horario(posicao) for posicao in ticks]
    eixo.xaxis.set_major_locator(FixedLocator(ticks))
    eixo.xaxis.set_major_formatter(FixedFormatter(rotulos))
    eixo.xaxis.set_minor_locator(NullLocator())
    eixo.xaxis.set_minor_formatter(NullFormatter())
    eixo.tick_params(axis="x", rotation=0, labelsize=9)
    for rotulo in eixo.get_xticklabels():
        rotulo.set_ha("center")
    eixo.tick_params(axis="y", labelsize=8)


def desenhar_volume_agora(
    eixo,
    figura,
    posicoes_x: list[float] | np.ndarray,
    pontos_tooltip: list[dict],
    xlim: tuple[float, float],
    *,
    largura_barra: float = _LARGURA_BARRA_VOLUME,
) -> int | None:
    """Desenha barras de volume abaixo do grafico de preco."""
    posicoes = np.asarray(posicoes_x, dtype=float)
    ultimo_volume: int | None = None

    for posicao, ponto in zip(posicoes, pontos_tooltip, strict=False):
        volume_bruto = ponto.get("volume")
        if volume_bruto is None:
            continue
        try:
            volume = int(volume_bruto)
        except (TypeError, ValueError):
            continue
        if volume <= 0:
            continue
        ultimo_volume = volume
        eixo.bar(
            float(posicao),
            volume,
            width=largura_barra,
            color=obter_cor_barra_volume(ponto),
            alpha=0.88,
            align="center",
            zorder=2,
        )

    ylim = calcular_limites_eixo_volume(pontos_tooltip)
    configurar_eixo_volume_agora(eixo, xlim, ylim)
    aplicar_grade_padrao_grafico(eixo, apenas_horizontal=True)
    aplicar_tema_matplotlib(eixo, figura)

    rotulo = formatar_volume_agora(ultimo_volume)
    cor_texto = CORES.get("textoSecundario", "#94A3B8")
    eixo.text(
        0.01,
        0.06,
        f"Volume  {rotulo}",
        transform=eixo.transAxes,
        va="bottom",
        ha="left",
        fontsize=8,
        color=cor_texto,
        zorder=5,
    )
    return ultimo_volume


def finalizar_figura_grafico_agora(
    eixo_preco,
    figura,
    titulo: str,
    *,
    com_painel_volume: bool = False,
) -> None:
    """Titulo, grade e margens do grafico Agora (com ou sem volume)."""
    aplicar_titulo_padrao_grafico(eixo_preco, titulo)
    aplicar_grade_padrao_grafico(eixo_preco, apenas_horizontal=True)
    aplicar_tema_matplotlib(eixo_preco, figura)
    if com_painel_volume:
        figura.subplots_adjust(
            bottom=max(0.10, MARGEM_GRAFICO_BOTTOM - 0.02),
            left=MARGEM_GRAFICO_LEFT,
            right=MARGEM_GRAFICO_RIGHT,
            top=MARGEM_GRAFICO_TOP,
            hspace=0.04,
        )
    else:
        figura.subplots_adjust(
            bottom=MARGEM_GRAFICO_BOTTOM,
            left=MARGEM_GRAFICO_LEFT,
            right=MARGEM_GRAFICO_RIGHT,
            top=MARGEM_GRAFICO_TOP,
        )


def desenhar_serie_agora(
    eixo,
    indices: np.ndarray,
    valores: list[float],
    pontos_tooltip: list[dict],
    *,
    modelo: ModeloGrafico | str,
    cor: str,
    y_base: float,
) -> Line2D:
    """Serie principal com area/linha no estilo Google."""
    valores_np = np.asarray(valores, dtype=float)
    modelo_txt = str(modelo).lower()

    if modelo_txt == "area":
        eixo.fill_between(
            indices,
            valores_np,
            y2=y_base,
            alpha=ALPHA_AREA_GRAFICO,
            color=cor,
            zorder=1,
        )
        eixo.plot(
            indices,
            valores_np,
            color=cor,
            linewidth=LARGURA_LINHA_GRAFICO,
            zorder=3,
        )
        marcar_ultimo_ponto_agora(eixo, indices, valores_np, cor)
        from src.View.grafico_modelo_helper import _linha_guia_interacao

        return _linha_guia_interacao(eixo, indices, valores, label="Preco")

    linha = desenhar_serie_preco_principal(
        eixo,
        indices,
        valores,
        pontos_tooltip,
        modelo=modelo,
        cor=cor,
        label="Preco",
    )
    if modelo_txt == "linha":
        marcar_ultimo_ponto_agora(eixo, indices, valores_np, cor)
    return linha
