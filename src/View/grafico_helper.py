"""Tooltip e selecao de periodo por clique nos graficos Matplotlib."""
from __future__ import annotations

from collections.abc import Callable

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.lines import Line2D

from src.View.formatadores import formatar_moeda
from src.View.painel_comparacao_periodo import (
    calcular_comparacao_acao_unica,
    calcular_comparacao_multiplas,
    payload_inicio_selecionado,
    payload_instrucao,
)

COR_VERMELHO = "#DC2626"
DESLOC_TOOLTIP_PONTOS = 18
MARGEM_TOOLTIP_FRACAO = 0.22


def _formatar_volume(volume: int | None) -> str:
    if volume is None:
        return "—"
    return f"{volume:,}".replace(",", ".")


def _criar_anotacao_tooltip(eixo):
    """Cria caixa de tooltip com recorte desligado para nao cortar nas bordas."""
    return eixo.annotate(
        "",
        xy=(0, 0),
        xytext=(DESLOC_TOOLTIP_PONTOS, DESLOC_TOOLTIP_PONTOS),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.5", fc="#EFF6FF", ec="#2563EB", alpha=0.98),
        arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1),
        fontsize=9,
        annotation_clip=False,
        clip_on=False,
    )


def _posicionar_tooltip(anotacao, eixo, x: float, y: float) -> None:
    """Desloca o tooltip para dentro da area visivel (evita corte a direita/em cima)."""
    xlim = eixo.get_xlim()
    ylim = eixo.get_ylim()
    largura = float(xlim[1] - xlim[0]) or 1.0
    altura = float(ylim[1] - ylim[0]) or 1.0
    frac_x = (float(x) - float(xlim[0])) / largura
    frac_y = (float(y) - float(ylim[0])) / altura

    desloc = DESLOC_TOOLTIP_PONTOS
    margem = MARGEM_TOOLTIP_FRACAO

    # Padrao: caixa acima e a direita do ponto.
    dx, dy = desloc, desloc
    ha, va = "left", "bottom"

    if frac_x >= 1.0 - margem:
        dx = -desloc
        ha = "right"
    elif frac_x <= margem:
        dx = desloc
        ha = "left"

    if frac_y >= 1.0 - margem:
        dy = -desloc
        va = "top"
    elif frac_y <= margem:
        dy = desloc
        va = "bottom"

    # Canto superior direito (ultimos pregões): abre para esquerda e para baixo.
    if frac_x >= 1.0 - margem and frac_y >= 0.45:
        dx = -desloc
        dy = -desloc
        ha = "right"
        va = "top"

    anotacao.xyann = (dx, dy)
    anotacao.set_ha(ha)
    anotacao.set_va(va)


def _indice_mais_proximo(evento, linha: Line2D, eixo) -> int | None:
    if evento.inaxes != eixo or evento.xdata is None:
        return None
    xs = np.array(linha.get_xdata(), dtype=float)
    if len(xs) == 0:
        return None
    indice = int(np.argmin(np.abs(xs - evento.xdata)))
    limiar = max((eixo.get_xlim()[1] - eixo.get_xlim()[0]) * 0.05, 0.3)
    if abs(xs[indice] - evento.xdata) > limiar:
        return None
    return indice


def _indice_por_eixo_x(evento, eixo, quantidade_pontos: int) -> int | None:
    if evento.inaxes != eixo or evento.xdata is None or quantidade_pontos <= 0:
        return None
    indice = int(round(evento.xdata))
    indice = max(0, min(indice, quantidade_pontos - 1))
    limiar = max((eixo.get_xlim()[1] - eixo.get_xlim()[0]) * 0.05, 0.3)
    if abs(indice - evento.xdata) > limiar:
        return None
    return indice


def _montar_texto_comparacao(
    pontos: list[dict],
    indice_inicio: int,
    indice_fim: int,
    simbolo: str,
    moeda: str,
) -> str:
    p_ini = pontos[indice_inicio]
    p_fim = pontos[indice_fim]
    preco_ini = float(p_ini["fechamento"])
    preco_fim = float(p_fim["fechamento"])
    variacao = preco_fim - preco_ini
    base = preco_ini if preco_ini else 1.0
    variacao_pct = (variacao / base) * 100
    sinal = "+" if variacao >= 0 else ""
    pregões = abs(indice_fim - indice_inicio) + 1
    codigo = simbolo.replace(".SA", "")
    return (
        f"{codigo}: {p_ini['data']} → {p_fim['data']} | "
        f"Inicial {formatar_moeda(preco_ini, moeda)} → Final {formatar_moeda(preco_fim, moeda)} | "
        f"Variacao {sinal}{formatar_moeda(variacao, moeda)} ({sinal}{variacao_pct:.2f}%) | "
        f"{pregões} pregões no intervalo"
    )


def _criar_estado_selecao() -> dict:
    return {"indices": [], "artistas": []}


def _limpar_artistas(estado: dict) -> None:
    for artista in estado["artistas"]:
        try:
            artista.remove()
        except Exception:
            pass
    estado["artistas"].clear()


def _desenhar_marcador_vermelho(eixo, estado: dict, x: float, y: float) -> None:
    marcador, = eixo.plot(
        x,
        y,
        marker="o",
        markersize=14,
        markerfacecolor=COR_VERMELHO,
        markeredgecolor="#FFFFFF",
        markeredgewidth=2,
        linestyle="None",
        zorder=6,
    )
    estado["artistas"].append(marcador)


def configurar_selecao_periodo(
    canvas: FigureCanvasTkAgg,
    eixo,
    linha: Line2D,
    pontos: list[dict],
    simbolo: str,
    moeda: str,
    ao_atualizar_comparacao: Callable[[dict], None],
    obter_quantidade_cotas: Callable[[], int] | None = None,
) -> None:
    """Clique duplo no grafico de uma acao (marcadores e intervalo vermelhos)."""
    estado = _criar_estado_selecao()

    def _quantidade_cotas() -> int:
        if obter_quantidade_cotas is None:
            return 1
        try:
            return max(1, int(obter_quantidade_cotas()))
        except (TypeError, ValueError):
            return 1

    def desenhar_marcador(indice: int) -> None:
        xs = np.array(linha.get_xdata(), dtype=float)
        ys = np.array(linha.get_ydata(), dtype=float)
        _desenhar_marcador_vermelho(eixo, estado, xs[indice], ys[indice])

    def desenhar_intervalo(indice_inicio: int, indice_fim: int) -> None:
        xs = np.array(linha.get_xdata(), dtype=float)
        ys = np.array(linha.get_ydata(), dtype=float)
        faixa = eixo.axvspan(
            indice_inicio - 0.35,
            indice_fim + 0.35,
            color=COR_VERMELHO,
            alpha=0.18,
            zorder=1,
        )
        trecho, = eixo.plot(
            xs[indice_inicio : indice_fim + 1],
            ys[indice_inicio : indice_fim + 1],
            color=COR_VERMELHO,
            linewidth=3.5,
            zorder=5,
        )
        estado["artistas"].extend([faixa, trecho])
        desenhar_marcador(indice_inicio)
        desenhar_marcador(indice_fim)

    def ao_clicar(evento):
        if evento.button != 1:
            return
        indice = _indice_mais_proximo(evento, linha, eixo)
        if indice is None:
            return

        selecionados = estado["indices"]
        if len(selecionados) >= 2:
            _limpar_artistas(estado)
            selecionados.clear()
            ao_atualizar_comparacao(
                payload_instrucao(
                    "Informe a quantidade de acoes. Clique no grafico: 1º ponto (inicio) "
                    "e 2º ponto (fim) para ver valor pago, valor final, lucro ou prejuizo."
                )
            )

        if len(selecionados) == 0:
            selecionados.append(indice)
            desenhar_marcador(indice)
            p = pontos[indice]
            ao_atualizar_comparacao(
                payload_inicio_selecionado(
                    p["data"],
                    float(p["fechamento"]),
                    moeda,
                    _quantidade_cotas(),
                )
            )
        elif len(selecionados) == 1:
            if indice == selecionados[0]:
                return
            selecionados.append(indice)
            indice_inicio = min(selecionados)
            indice_fim = max(selecionados)
            _limpar_artistas(estado)
            desenhar_intervalo(indice_inicio, indice_fim)
            ao_atualizar_comparacao(
                calcular_comparacao_acao_unica(
                    pontos,
                    simbolo,
                    moeda,
                    indice_inicio,
                    indice_fim,
                    _quantidade_cotas(),
                )
            )
        canvas.draw_idle()

    canvas.mpl_connect("button_press_event", ao_clicar)
    ao_atualizar_comparacao(
        payload_instrucao(
            "Informe a quantidade de acoes. Clique no grafico: 1º ponto (inicio) "
            "e 2º ponto (fim) para ver valor pago, valor final, lucro ou prejuizo."
        )
    )


def configurar_selecao_periodo_comparacao(
    canvas: FigureCanvasTkAgg,
    eixo,
    linhas_grafico: list[Line2D],
    series: dict[str, list[dict]],
    simbolos: list[str],
    ao_atualizar_comparacao: Callable[[dict], None],
) -> None:
    """Mesma logica de selecao vermelha, aplicada a todas as linhas do grafico comparativo."""
    if not simbolos or not linhas_grafico:
        return

    estado = _criar_estado_selecao()
    quantidade = len(series[simbolos[0]])

    def desenhar_marcadores_no_indice(indice: int) -> None:
        for linha in linhas_grafico:
            xs = np.array(linha.get_xdata(), dtype=float)
            ys = np.array(linha.get_ydata(), dtype=float)
            if indice < len(xs):
                _desenhar_marcador_vermelho(eixo, estado, xs[indice], ys[indice])

    def desenhar_intervalo(indice_inicio: int, indice_fim: int) -> None:
        faixa = eixo.axvspan(
            indice_inicio - 0.35,
            indice_fim + 0.35,
            color=COR_VERMELHO,
            alpha=0.18,
            zorder=1,
        )
        estado["artistas"].append(faixa)

        for linha in linhas_grafico:
            xs = np.array(linha.get_xdata(), dtype=float)
            ys = np.array(linha.get_ydata(), dtype=float)
            trecho, = eixo.plot(
                xs[indice_inicio : indice_fim + 1],
                ys[indice_inicio : indice_fim + 1],
                color=COR_VERMELHO,
                linewidth=3.5,
                zorder=5,
            )
            estado["artistas"].append(trecho)

        desenhar_marcadores_no_indice(indice_inicio)
        desenhar_marcadores_no_indice(indice_fim)

    def ao_clicar(evento):
        if evento.button != 1:
            return
        indice = _indice_por_eixo_x(evento, eixo, quantidade)
        if indice is None:
            return

        selecionados = estado["indices"]
        if len(selecionados) >= 2:
            _limpar_artistas(estado)
            selecionados.clear()
            ao_atualizar_comparacao(
                payload_instrucao(
                    "Clique no grafico: 1º ponto (inicio) e 2º ponto (fim) para comparar o periodo."
                )
            )

        if len(selecionados) == 0:
            selecionados.append(indice)
            desenhar_marcadores_no_indice(indice)
            data_ref = series[simbolos[0]][indice]["data"]
            ao_atualizar_comparacao(payload_inicio_selecionado(data_ref))
        elif len(selecionados) == 1:
            if indice == selecionados[0]:
                return
            selecionados.append(indice)
            indice_inicio = min(selecionados)
            indice_fim = max(selecionados)
            _limpar_artistas(estado)
            desenhar_intervalo(indice_inicio, indice_fim)
            ao_atualizar_comparacao(
                calcular_comparacao_multiplas(series, simbolos, indice_inicio, indice_fim)
            )
        canvas.draw_idle()

    canvas.mpl_connect("button_press_event", ao_clicar)
    ao_atualizar_comparacao(
        payload_instrucao(
            "Clique no grafico: 1º ponto (inicio) e 2º ponto (fim) para comparar o periodo entre as acoes."
        )
    )


def configurar_tooltip_acao(
    canvas: FigureCanvasTkAgg,
    eixo,
    linha: Line2D,
    pontos: list[dict],
    simbolo: str,
    moeda: str = "BRL",
) -> None:
    def texto_tooltip(indice: int) -> str:
        p = pontos[indice]
        linhas = [
            simbolo.replace(".SA", ""),
            f"Data: {p['data']}",
            f"Fechamento: {formatar_moeda(p['fechamento'], moeda)}",
        ]
        if p.get("abertura") is not None:
            linhas.append(f"Abertura: {formatar_moeda(p['abertura'], moeda)}")
        if p.get("volume") is not None:
            linhas.append(f"Volume: {_formatar_volume(p['volume'])}")
        return "\n".join(linhas)

    _configurar_tooltip(eixo, canvas, linha, texto_tooltip)


def configurar_tooltip_comparacao(
    canvas: FigureCanvasTkAgg,
    eixo,
    linhas_grafico: list[Line2D],
    series: dict[str, list[dict]],
    simbolos: list[str],
) -> None:
    anotacao = _criar_anotacao_tooltip(eixo)
    anotacao.set_visible(False)

    def texto_tooltip(indice_linha: int, indice_ponto: int) -> str:
        simbolo = simbolos[indice_linha]
        p = series[simbolo][indice_ponto]
        moeda = "BRL" if simbolo.endswith(".SA") else "USD"
        return "\n".join(
            [
                simbolo.replace(".SA", ""),
                f"Data: {p['data']}",
                f"Preco: {formatar_moeda(p['preco'], moeda)}",
                f"Indice relativo: {p['indice_relativo']:.2f}",
            ]
        )

    def ao_mover(evento):
        if evento.inaxes != eixo or evento.xdata is None or evento.ydata is None:
            if anotacao.get_visible():
                anotacao.set_visible(False)
                canvas.draw_idle()
            return

        melhor_dist = float("inf")
        melhor_linha = None
        melhor_indice = None
        melhor_xy = None

        for idx_linha, linha in enumerate(linhas_grafico):
            xs = np.array(linha.get_xdata(), dtype=float)
            ys = np.array(linha.get_ydata(), dtype=float)
            if len(xs) == 0:
                continue
            distancias = np.hypot(xs - evento.xdata, ys - evento.ydata)
            indice = int(np.argmin(distancias))
            dist = float(distancias[indice])
            if dist < melhor_dist:
                melhor_dist = dist
                melhor_linha = idx_linha
                melhor_indice = indice
                melhor_xy = (xs[indice], ys[indice])

        limiar = max((eixo.get_xlim()[1] - eixo.get_xlim()[0]) * 0.08, 0.5)
        if melhor_linha is None or melhor_dist > limiar:
            if anotacao.get_visible():
                anotacao.set_visible(False)
                canvas.draw_idle()
            return

        anotacao.xy = melhor_xy
        anotacao.set_text(texto_tooltip(melhor_linha, melhor_indice))
        _posicionar_tooltip(anotacao, eixo, melhor_xy[0], melhor_xy[1])
        anotacao.set_visible(True)
        canvas.draw_idle()

    canvas.mpl_connect("motion_notify_event", ao_mover)


def _configurar_tooltip(eixo, canvas, linha, texto_fn) -> None:
    anotacao = _criar_anotacao_tooltip(eixo)
    anotacao.set_visible(False)

    def ao_mover(evento):
        if evento.inaxes != eixo or evento.xdata is None:
            if anotacao.get_visible():
                anotacao.set_visible(False)
                canvas.draw_idle()
            return

        xs = np.array(linha.get_xdata(), dtype=float)
        ys = np.array(linha.get_ydata(), dtype=float)
        if len(xs) == 0:
            return

        indice = int(np.argmin(np.abs(xs - evento.xdata)))
        limiar = max((eixo.get_xlim()[1] - eixo.get_xlim()[0]) * 0.05, 0.3)
        if abs(xs[indice] - evento.xdata) > limiar:
            if anotacao.get_visible():
                anotacao.set_visible(False)
                canvas.draw_idle()
            return

        x_ponto = float(xs[indice])
        y_ponto = float(ys[indice])
        anotacao.xy = (x_ponto, y_ponto)
        anotacao.set_text(texto_fn(indice))
        _posicionar_tooltip(anotacao, eixo, x_ponto, y_ponto)
        anotacao.set_visible(True)
        canvas.draw_idle()

    canvas.mpl_connect("motion_notify_event", ao_mover)
