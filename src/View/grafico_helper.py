"""Tooltip e selecao de periodo por clique nos graficos Matplotlib."""
from __future__ import annotations

import re
import threading
from collections.abc import Callable
from copy import deepcopy

import matplotlib.transforms as mtransforms
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter, NullLocator

from src.Tool.janela_helper import agendar_na_ui
from src.View.formatadores import formatar_moeda
from src.View.grafico_zoom_helper import consumir_arraste_pan
from src.View.tema import CORES
from src.View.painel_comparacao_periodo import (
    calcular_comparacao_acao_unica,
    calcular_comparacao_multiplas,
    enriquecer_comparacao_com_cdi,
    payload_inicio_selecionado,
    payload_instrucao,
)

TEXTO_INSTRUCAO_GRAFICO_ACAO = (
    "Informe a quantidade de acoes. Clique no grafico: 1º ponto (inicio) "
    "e 2º ponto (fim) para ver valor pago, valor final, lucro ou prejuizo "
    "e comparacao com 100% do CDI no mesmo periodo (acoes em reais)."
)

COR_VERMELHO = "#DC2626"
COR_LINHA_CDI = "#D97706"
DESLOC_TOOLTIP_PONTOS = 18
MARGEM_TOOLTIP_FRACAO = 0.22


def aplicar_tema_matplotlib(eixo, figura=None) -> None:
    """Aplica cores de texto, eixos e legenda conforme modo claro/escuro (CORES)."""
    cor_texto = CORES["texto"]
    cor_borda = CORES["borda"]
    fundo_grafico = CORES.get("graficoFundo", CORES["superficie"])

    if figura is not None:
        figura.set_facecolor(fundo_grafico)

    eixo.set_facecolor(fundo_grafico)

    titulo = eixo.get_title()
    if titulo:
        eixo.title.set_color(cor_texto)

    rotulo_y = eixo.get_ylabel()
    if rotulo_y:
        eixo.yaxis.label.set_color(cor_texto)

    rotulo_x = eixo.get_xlabel()
    if rotulo_x:
        eixo.xaxis.label.set_color(cor_texto)

    eixo.tick_params(axis="x", colors=cor_texto, labelcolor=cor_texto)
    eixo.tick_params(axis="y", colors=cor_texto, labelcolor=cor_texto)

    for rotulo in eixo.get_xticklabels():
        rotulo.set_color(cor_texto)
    for rotulo in eixo.get_yticklabels():
        rotulo.set_color(cor_texto)

    for spine in eixo.spines.values():
        spine.set_color(cor_borda)

    legenda = eixo.get_legend()
    if legenda is not None:
        moldura = legenda.get_frame()
        moldura.set_facecolor(fundo_grafico)
        moldura.set_edgecolor(cor_borda)
        for texto in legenda.get_texts():
            texto.set_color(cor_texto)


HORA_INICIO_PREGAO_AGORA = 10
HORA_FIM_PREGAO_AGORA = 18
INTERVALO_TICKS_HORARIO_AGORA = 2


def horario_para_minutos_dia(horario: str) -> float | None:
    """Converte HH:MM em minutos desde a meia-noite."""
    texto = str(horario or "").strip()
    if not re.match(r"^\d{2}:\d{2}", texto):
        texto = extrair_horario_exibicao(texto)
    try:
        hora, minuto = map(int, texto.split(":")[:2])
        if hora < 0 or hora > 23 or minuto < 0 or minuto > 59:
            return None
        return float(hora * 60 + minuto)
    except (ValueError, TypeError):
        return None


def minutos_dia_para_horario(minutos: float) -> str:
    """Converte minutos desde a meia-noite em HH:MM."""
    total = max(0, int(round(minutos)))
    hora = (total // 60) % 24
    minuto = total % 60
    return f"{hora:02d}:{minuto:02d}"


def extrair_minutos_dia_de_ponto(data_exibicao: str, *, data_iso: str | None = None) -> float | None:
    """Obtem minutos do dia a partir de data_exibicao ou data_iso."""
    horario = extrair_horario_exibicao(data_exibicao, data_iso=data_iso)
    return horario_para_minutos_dia(horario)


def configurar_eixo_horario_pregao_agora(
    eixo,
    *,
    hora_inicio: int = HORA_INICIO_PREGAO_AGORA,
    hora_fim: int = HORA_FIM_PREGAO_AGORA,
    intervalo_horas: int = INTERVALO_TICKS_HORARIO_AGORA,
) -> None:
    """Fixa o eixo X no horario de pregao (ex.: 10:00 ate 18:00) com ticks a cada 2 h."""
    inicio = hora_inicio * 60
    fim = hora_fim * 60
    passo = max(1, intervalo_horas) * 60
    ticks = list(range(inicio, fim + 1, passo))
    rotulos = [minutos_dia_para_horario(posicao) for posicao in ticks]

    eixo.set_xlim(inicio, fim)
    eixo.xaxis.set_major_locator(FixedLocator(ticks))
    eixo.xaxis.set_major_formatter(FixedFormatter(rotulos))
    eixo.xaxis.set_minor_locator(NullLocator())
    eixo.xaxis.set_minor_formatter(NullFormatter())
    eixo.tick_params(axis="x", rotation=0, labelsize=9)
    for rotulo in eixo.get_xticklabels():
        rotulo.set_ha("center")


def extrair_horario_exibicao(texto: str, *, data_iso: str | None = None) -> str:
    """Extrai HH:MM de data_exibicao ou data_iso para graficos intraday."""
    limpo = str(texto or "").strip()
    correspondencia = re.match(r"^\d{2}/\d{2}/\d{4}\s+(\d{2}:\d{2})", limpo)
    if correspondencia:
        return correspondencia.group(1)
    if re.match(r"^\d{2}:\d{2}", limpo):
        return limpo[:5]
    if data_iso:
        try:
            from datetime import datetime

            bruto = str(data_iso).replace("Z", "+00:00")
            dt = datetime.fromisoformat(bruto)
            return dt.strftime("%H:%M")
        except Exception:
            pass
    return limpo


def _formatar_rotulo_data_eixo(texto: str) -> str:
    """Exibe so dd/mm/aaaa no eixo (remove hora 00:00 duplicada visualmente)."""
    limpo = str(texto or "").strip()
    if re.match(r"^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}", limpo):
        return limpo[:10]
    return limpo


def configurar_rotulos_eixo_x(
    eixo,
    labels: list[str],
    *,
    rotacao: int = 25,
    tamanho_fonte: int = 8,
    max_rotulos: int = 10,
    somente_horario: bool = False,
) -> None:
    """
    Define rotulos espacados no eixo X com FixedLocator (evita ticks duplicados).
    """
    quantidade = len(labels)
    if quantidade == 0:
        return

    if somente_horario:
        rotulos = [extrair_horario_exibicao(item) for item in labels]
    else:
        rotulos = [_formatar_rotulo_data_eixo(item) for item in labels]
    if quantidade <= max_rotulos:
        posicoes = list(range(quantidade))
    else:
        passo = max(1, quantidade // max_rotulos)
        posicoes = list(range(0, quantidade, passo))
        if posicoes[-1] != quantidade - 1:
            posicoes.append(quantidade - 1)

    rotulos_posicoes = [rotulos[indice] for indice in posicoes]
    eixo.xaxis.set_major_locator(FixedLocator(posicoes))
    eixo.xaxis.set_major_formatter(FixedFormatter(rotulos_posicoes))
    eixo.xaxis.set_minor_locator(NullLocator())
    eixo.xaxis.set_minor_formatter(NullFormatter())
    eixo.tick_params(axis="x", rotation=rotacao, labelsize=tamanho_fonte)
    for rotulo in eixo.get_xticklabels():
        rotulo.set_ha("right")


def _formatar_volume(volume: int | None) -> str:
    if volume is None:
        return "—"
    return f"{volume:,}".replace(",", ".")


def _cor_guia_mouse_grafico() -> str:
    return CORES.get("primariaHover", CORES["primaria"])


def _criar_anotacao_tooltip(eixo):
    """Cria caixa de tooltip com borda tracejada e recorte desligado."""
    cor = _cor_guia_mouse_grafico()
    return eixo.annotate(
        "",
        xy=(0, 0),
        xytext=(DESLOC_TOOLTIP_PONTOS, DESLOC_TOOLTIP_PONTOS),
        textcoords="offset points",
        bbox=dict(
            boxstyle="round,pad=0.5",
            fc=CORES.get("graficoTooltipFundo", CORES["infoFundo"]),
            ec=cor,
            linestyle="--",
            linewidth=1.2,
            alpha=0.98,
        ),
        arrowprops=dict(arrowstyle="-", color=cor, linestyle="--", lw=1),
        fontsize=9,
        color=CORES["texto"],
        annotation_clip=False,
        clip_on=False,
    )


def _gesto_pan_ativo(canvas: FigureCanvasTkAgg) -> bool:
    gesto = getattr(canvas, "_gesto_pan", None)
    return bool(gesto and gesto.get("ativo"))


def _criar_guia_mouse(eixo) -> dict:
    """Linhas tracejadas, faixa vertical e marcador do ponto sob o mouse."""
    cor = _cor_guia_mouse_grafico()
    trans_vertical = mtransforms.blended_transform_factory(eixo.transData, eixo.transAxes)
    trans_horizontal = mtransforms.blended_transform_factory(eixo.transAxes, eixo.transData)

    retangulo = Rectangle(
        (0, 0),
        0.8,
        1,
        fill=True,
        facecolor=cor,
        edgecolor=cor,
        linestyle="--",
        linewidth=1.2,
        alpha=0.14,
        visible=False,
        zorder=4,
    )
    linha_vertical = Line2D(
        [0, 0],
        [0, 1],
        transform=trans_vertical,
        color=cor,
        linestyle="--",
        linewidth=1.1,
        alpha=0.9,
        visible=False,
        zorder=8,
    )
    linha_horizontal = Line2D(
        [0, 1],
        [0, 0],
        transform=trans_horizontal,
        color=cor,
        linestyle="--",
        linewidth=1.1,
        alpha=0.9,
        visible=False,
        zorder=8,
    )
    marcador, = eixo.plot(
        [],
        [],
        marker="o",
        markersize=9,
        markerfacecolor=cor,
        markeredgecolor="#FFFFFF",
        markeredgewidth=1.5,
        linestyle="None",
        visible=False,
        zorder=9,
    )
    anotacao = _criar_anotacao_tooltip(eixo)
    anotacao.set_visible(False)

    eixo.add_patch(retangulo)
    eixo.add_line(linha_vertical)
    eixo.add_line(linha_horizontal)

    return {
        "retangulo": retangulo,
        "linha_vertical": linha_vertical,
        "linha_horizontal": linha_horizontal,
        "marcador": marcador,
        "anotacao": anotacao,
    }


def _esconder_guia_mouse(guia: dict, canvas: FigureCanvasTkAgg) -> None:
    alterou = False
    for chave in ("retangulo", "linha_vertical", "linha_horizontal", "marcador", "anotacao"):
        artista = guia[chave]
        if artista.get_visible():
            artista.set_visible(False)
            alterou = True
    if alterou:
        canvas.draw_idle()


def _atualizar_guia_mouse(
    guia: dict,
    eixo,
    canvas: FigureCanvasTkAgg,
    x_ponto: float,
    y_ponto: float,
    texto: str,
) -> None:
    ylim = eixo.get_ylim()
    guia["retangulo"].set_xy((x_ponto - 0.4, ylim[0]))
    guia["retangulo"].set_height(ylim[1] - ylim[0])
    guia["retangulo"].set_visible(True)

    guia["linha_vertical"].set_data([x_ponto, x_ponto], [0, 1])
    guia["linha_vertical"].set_visible(True)
    guia["linha_horizontal"].set_data([0, 1], [y_ponto, y_ponto])
    guia["linha_horizontal"].set_visible(True)

    guia["marcador"].set_data([x_ponto], [y_ponto])
    guia["marcador"].set_visible(True)

    anotacao = guia["anotacao"]
    anotacao.xy = (x_ponto, y_ponto)
    anotacao.set_text(texto)
    _posicionar_tooltip(anotacao, eixo, x_ponto, y_ponto)
    anotacao.set_visible(True)
    canvas.draw_idle()


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


def _publicar_payload_com_cdi(
    canvas: FigureCanvasTkAgg,
    payload: dict,
    ao_atualizar_comparacao: Callable[[dict], None],
) -> None:
    """Atualiza o painel e busca CDI em thread para nao travar a interface."""
    ao_atualizar_comparacao(payload)
    if payload.get("tipo") != "completo" or not payload.get("comparar_cdi"):
        return

    widget_raiz = canvas.get_tk_widget()

    def trabalho() -> None:
        copia_loading = deepcopy(payload)
        if copia_loading.get("uma_acao") and copia_loading.get("acoes"):
            copia_loading["acoes"][0]["cdi_carregando"] = True
        else:
            copia_loading["cdi_carregando"] = True
        agendar_na_ui(widget_raiz, lambda: ao_atualizar_comparacao(copia_loading))
        enriquecido = enriquecer_comparacao_com_cdi(deepcopy(payload))
        agendar_na_ui(widget_raiz, lambda p=enriquecido: ao_atualizar_comparacao(p))

    threading.Thread(target=trabalho, daemon=True).start()


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
        if consumir_arraste_pan(canvas):
            return
        indice = _indice_mais_proximo(evento, linha, eixo)
        if indice is None:
            return

        selecionados = estado["indices"]
        if len(selecionados) >= 2:
            _limpar_artistas(estado)
            selecionados.clear()
            ao_atualizar_comparacao(payload_instrucao(TEXTO_INSTRUCAO_GRAFICO_ACAO))

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
            _publicar_payload_com_cdi(
                canvas,
                calcular_comparacao_acao_unica(
                    pontos,
                    simbolo,
                    moeda,
                    indice_inicio,
                    indice_fim,
                    _quantidade_cotas(),
                ),
                ao_atualizar_comparacao,
            )
        canvas.draw_idle()

    canvas.mpl_connect("button_release_event", ao_clicar)
    ao_atualizar_comparacao(payload_instrucao(TEXTO_INSTRUCAO_GRAFICO_ACAO))


TEXTO_INSTRUCAO_GRAFICO_COMPARACAO = (
    "Clique no grafico: 1º ponto (inicio) e 2º ponto (fim) para comparar o periodo entre as acoes "
    "e ver o rendimento do CDI no mesmo intervalo."
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
        if consumir_arraste_pan(canvas):
            return
        indice = _indice_por_eixo_x(evento, eixo, quantidade)
        if indice is None:
            return

        selecionados = estado["indices"]
        if len(selecionados) >= 2:
            _limpar_artistas(estado)
            selecionados.clear()
            ao_atualizar_comparacao(payload_instrucao(TEXTO_INSTRUCAO_GRAFICO_COMPARACAO))

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
            _publicar_payload_com_cdi(
                canvas,
                calcular_comparacao_multiplas(series, simbolos, indice_inicio, indice_fim),
                ao_atualizar_comparacao,
            )
        canvas.draw_idle()

    canvas.mpl_connect("button_release_event", ao_clicar)
    ao_atualizar_comparacao(payload_instrucao(TEXTO_INSTRUCAO_GRAFICO_COMPARACAO))


def configurar_tooltip_acao(
    canvas: FigureCanvasTkAgg,
    eixo,
    linha: Line2D,
    pontos: list[dict],
    simbolo: str,
    moeda: str = "BRL",
    *,
    somente_horario: bool = False,
) -> None:
    def texto_tooltip(indice: int) -> str:
        p = pontos[indice]
        if somente_horario:
            rotulo_tempo = "Horario"
            data = extrair_horario_exibicao(
                str(p.get("data", "")),
                data_iso=p.get("data_iso"),
            )
        else:
            rotulo_tempo = "Data"
            data = _formatar_rotulo_data_eixo(p["data"])
        valor = formatar_moeda(p["fechamento"], moeda)
        linhas = [
            f"{rotulo_tempo}: {data}",
            f"Valor: {valor}",
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
    guia = _criar_guia_mouse(eixo)

    def texto_tooltip(indice_linha: int, indice_ponto: int) -> str:
        simbolo = simbolos[indice_linha]
        p = series[simbolo][indice_ponto]
        moeda = "BRL" if simbolo.endswith(".SA") else "USD"
        data = _formatar_rotulo_data_eixo(p["data"])
        valor = formatar_moeda(p["preco"], moeda)
        return "\n".join(
            [
                simbolo.replace(".SA", ""),
                f"Data: {data}",
                f"Valor: {valor}",
                f"Indice relativo: {p['indice_relativo']:.2f}",
            ]
        )

    def ao_mover(evento):
        if _gesto_pan_ativo(canvas):
            _esconder_guia_mouse(guia, canvas)
            return
        if evento.inaxes != eixo or evento.xdata is None or evento.ydata is None:
            _esconder_guia_mouse(guia, canvas)
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
            _esconder_guia_mouse(guia, canvas)
            return

        _atualizar_guia_mouse(
            guia,
            eixo,
            canvas,
            float(melhor_xy[0]),
            float(melhor_xy[1]),
            texto_tooltip(melhor_linha, melhor_indice),
        )

    def ao_sair(_evento) -> None:
        _esconder_guia_mouse(guia, canvas)

    canvas.mpl_connect("motion_notify_event", ao_mover)
    canvas.mpl_connect("axes_leave_event", ao_sair)


def _desconectar_eventos_tooltip(canvas: FigureCanvasTkAgg) -> None:
    """Remove handlers de tooltip anteriores para evitar duplicacao ao atualizar o grafico."""
    ids = getattr(canvas, "_ids_tooltip_grafico", None)
    if not ids:
        return
    for identificador in ids:
        try:
            canvas.mpl_disconnect(identificador)
        except Exception:
            pass
    canvas._ids_tooltip_grafico = []


def _configurar_tooltip(eixo, canvas, linha, texto_fn) -> None:
    _desconectar_eventos_tooltip(canvas)
    guia = _criar_guia_mouse(eixo)

    def ao_mover(evento):
        if _gesto_pan_ativo(canvas):
            _esconder_guia_mouse(guia, canvas)
            return
        if evento.inaxes != eixo or evento.xdata is None:
            _esconder_guia_mouse(guia, canvas)
            return

        xs = np.array(linha.get_xdata(), dtype=float)
        ys = np.array(linha.get_ydata(), dtype=float)
        if len(xs) == 0:
            return

        indice = int(np.argmin(np.abs(xs - evento.xdata)))
        limiar = max((eixo.get_xlim()[1] - eixo.get_xlim()[0]) * 0.05, 0.3)
        if abs(xs[indice] - evento.xdata) > limiar:
            _esconder_guia_mouse(guia, canvas)
            return

        x_ponto = float(xs[indice])
        y_ponto = float(ys[indice])
        _atualizar_guia_mouse(guia, eixo, canvas, x_ponto, y_ponto, texto_fn(indice))

    def ao_sair(_evento) -> None:
        _esconder_guia_mouse(guia, canvas)

    cid_mover = canvas.mpl_connect("motion_notify_event", ao_mover)
    cid_sair = canvas.mpl_connect("axes_leave_event", ao_sair)
    canvas._ids_tooltip_grafico = [cid_mover, cid_sair]
