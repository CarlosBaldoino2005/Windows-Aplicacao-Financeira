"""Ferramentas de desenho para analise tecnica nos graficos Matplotlib."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.lines import Line2D

from src.View.botao_helper import estilo_botao_padrao
from src.View.formatadores import formatar_moeda
from src.View.grafico_zoom_helper import consumir_arraste_pan
from src.View.grafico_marcador_cruz_helper import reaplicar_marcador_cruz_canvas
from src.View.tema import CORES

FerramentaAnalise = Literal["navegar", "fibonacci", "tendencia", "horizontal"]

_FERRAMENTAS_UI: tuple[tuple[FerramentaAnalise, str], ...] = (
    ("navegar", "Navegar"),
    ("fibonacci", "Fibonacci"),
    ("tendencia", "Linha de tendencia"),
    ("horizontal", "Linha horizontal"),
)

_NIVEIS_FIBONACCI: tuple[tuple[float, str], ...] = (
    (0.0, "0.0"),
    (0.236, "23.6"),
    (0.382, "38.2"),
    (0.5, "50.0"),
    (0.618, "61.8"),
    (0.786, "78.6"),
    (1.0, "100.0"),
)

_INSTRUCOES: dict[FerramentaAnalise, str] = {
    "navegar": "Zoom, arraste e selecao de periodo no grafico.",
    "fibonacci": "Clique no ponto inicial e depois no ponto final da perna (ex.: fundo e topo).",
    "tendencia": "Clique em dois pontos para desenhar uma linha de tendencia.",
    "horizontal": "Clique no grafico para marcar um nivel horizontal de suporte/resistencia.",
}


def ferramenta_analise_ativa(canvas: FigureCanvasTkAgg) -> FerramentaAnalise:
    """Retorna a ferramenta selecionada no canvas (padrao: navegar)."""
    texto = getattr(canvas, "_ferramenta_analise_ativa", "navegar")
    for chave, _ in _FERRAMENTAS_UI:
        if chave == texto:
            return chave
    return "navegar"


def ferramenta_analise_bloqueia_selecao_periodo(canvas: FigureCanvasTkAgg) -> bool:
    """Indica se a selecao de periodo deve ser ignorada (ferramenta de desenho ativa)."""
    return ferramenta_analise_ativa(canvas) != "navegar"


def limpar_ferramentas_analise_no_grafico(canvas: FigureCanvasTkAgg) -> bool:
    """Remove desenhos de analise do grafico (ex.: botao Reset do zoom)."""
    gerenciador = getattr(canvas, "_gerenciador_ferramentas_analise", None)
    if gerenciador is None:
        return False
    return gerenciador.limpar()


def _cor_ferramenta_analise() -> str:
    return CORES.get("info", "#3B82F6")


@dataclass
class _DesenhoFibonacci:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class _DesenhoTendencia:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class _DesenhoHorizontal:
    y: float


@dataclass
class GerenciadorFerramentasAnaliseGrafico:
    """Desenha e reaplica Fibonacci, tendencia e linhas horizontais no eixo de preco."""

    moeda: str = "BRL"
    formatar_rotulo_y: Callable[[float], str] | None = None
    _ferramenta: FerramentaAnalise = "navegar"
    _desenhos: list = field(default_factory=list)
    _artistas: list = field(default_factory=list)
    _ponto_pendente: tuple[float, float] | None = None
    _marcador_pendente: Line2D | None = None
    _ids_eventos: list[int] = field(default_factory=list)
    _canvas_ref: FigureCanvasTkAgg | None = None
    _eixo_ref: object | None = None

    def definir_ferramenta(self, ferramenta: FerramentaAnalise) -> None:
        self._ferramenta = ferramenta
        self._cancelar_ponto_pendente()

    def ferramenta_atual(self) -> FerramentaAnalise:
        return self._ferramenta

    def exportar_estado(self) -> tuple[FerramentaAnalise, list, tuple[float, float] | None]:
        """Guarda desenhos antes de recriar o canvas."""
        return self._ferramenta, list(self._desenhos), self._ponto_pendente

    def importar_estado(
        self,
        ferramenta: FerramentaAnalise,
        desenhos: list,
        ponto_pendente: tuple[float, float] | None = None,
    ) -> None:
        """Restaura desenhos apos recriar o canvas."""
        self._ferramenta = ferramenta
        self._desenhos = list(desenhos)
        self._ponto_pendente = ponto_pendente

    def limpar(self, *, redesenhar: bool = True) -> bool:
        havia = bool(self._desenhos or self._artistas or self._ponto_pendente)
        self._desenhos.clear()
        self._remover_artistas()
        self._cancelar_ponto_pendente()
        if redesenhar and self._canvas_ref is not None:
            self._canvas_ref.draw_idle()
        return havia

    def configurar_eventos(self, canvas: FigureCanvasTkAgg, eixo) -> None:
        """Registra cliques no canvas para desenhar conforme a ferramenta ativa."""
        self._canvas_ref = canvas
        self._eixo_ref = eixo
        canvas._gerenciador_ferramentas_analise = self
        self._desconectar_eventos()

        def ao_clicar(evento) -> None:
            if evento.button != 1:
                return
            if self._ferramenta == "navegar":
                return
            if getattr(evento, "inaxes", None) is not eixo:
                return
            if evento.xdata is None or evento.ydata is None:
                return
            if consumir_arraste_pan(canvas):
                return

            x = float(evento.xdata)
            y = float(evento.ydata)

            if self._ferramenta == "horizontal":
                self._desenhos.append(_DesenhoHorizontal(y=y))
                self._cancelar_ponto_pendente()
                self.reaplicar(eixo)
                return

            if self._ponto_pendente is None:
                self._ponto_pendente = (x, y)
                self._desenhar_marcador_pendente(eixo, x, y)
                canvas.draw_idle()
                return

            x1, y1 = self._ponto_pendente
            self._cancelar_ponto_pendente()
            if self._ferramenta == "fibonacci":
                self._desenhos.append(_DesenhoFibonacci(x1=x1, y1=y1, x2=x, y2=y))
            elif self._ferramenta == "tendencia":
                self._desenhos.append(_DesenhoTendencia(x1=x1, y1=y1, x2=x, y2=y))
            self.reaplicar(eixo)

        cid = canvas.mpl_connect("button_release_event", ao_clicar)
        self._ids_eventos.append(cid)

    def reaplicar(self, eixo) -> None:
        """Redesenha todas as ferramentas apos atualizar o grafico."""
        self._eixo_ref = eixo
        self._remover_artistas()
        for desenho in self._desenhos:
            if isinstance(desenho, _DesenhoFibonacci):
                self._renderizar_fibonacci(eixo, desenho)
            elif isinstance(desenho, _DesenhoTendencia):
                self._renderizar_tendencia(eixo, desenho)
            elif isinstance(desenho, _DesenhoHorizontal):
                self._renderizar_horizontal(eixo, desenho)
        if self._ponto_pendente is not None:
            x, y = self._ponto_pendente
            self._desenhar_marcador_pendente(eixo, x, y)
        if self._canvas_ref is not None:
            self._canvas_ref.draw_idle()

    def _desconectar_eventos(self) -> None:
        canvas = getattr(self, "_canvas_ref", None)
        if canvas is None:
            self._ids_eventos.clear()
            return
        for identificador in self._ids_eventos:
            try:
                canvas.mpl_disconnect(identificador)
            except Exception:
                pass
        self._ids_eventos.clear()

    def _remover_artistas(self) -> None:
        for artista in self._artistas:
            try:
                artista.remove()
            except Exception:
                pass
        self._artistas.clear()
        self._marcador_pendente = None

    def _cancelar_ponto_pendente(self) -> None:
        self._ponto_pendente = None
        if self._marcador_pendente is not None:
            try:
                self._marcador_pendente.remove()
            except Exception:
                pass
            self._marcador_pendente = None

    def _desenhar_marcador_pendente(self, eixo, x: float, y: float) -> None:
        if self._marcador_pendente is not None:
            try:
                self._marcador_pendente.remove()
            except Exception:
                pass
        cor = _cor_ferramenta_analise()
        marcador, = eixo.plot(
            [x],
            [y],
            marker="o",
            markersize=7,
            markerfacecolor=cor,
            markeredgecolor=CORES.get("superficie", "#FFFFFF"),
            markeredgewidth=1.2,
            linestyle="None",
            zorder=9,
        )
        self._marcador_pendente = marcador
        self._artistas.append(marcador)

    def _formatar_y(self, valor: float) -> str:
        if self.formatar_rotulo_y is not None:
            return self.formatar_rotulo_y(valor)
        return formatar_moeda(valor, self.moeda)

    def _renderizar_fibonacci(self, eixo, desenho: _DesenhoFibonacci) -> None:
        cor = _cor_ferramenta_analise()
        x1, y1, x2, y2 = desenho.x1, desenho.y1, desenho.x2, desenho.y2
        linha_diag, = eixo.plot(
            [x1, x2],
            [y1, y2],
            color=cor,
            linewidth=1.2,
            alpha=0.95,
            zorder=7,
        )
        self._artistas.append(linha_diag)

        topo = max(y1, y2)
        base = min(y1, y2)
        amplitude = topo - base
        if amplitude <= 0:
            amplitude = max(abs(topo) * 0.001, 0.01)

        xlim = eixo.get_xlim()
        x_rotulo = xlim[1]

        for nivel, rotulo in _NIVEIS_FIBONACCI:
            preco = topo - nivel * amplitude
            linha = eixo.axhline(
                preco,
                color=cor,
                linewidth=0.9,
                alpha=0.88,
                zorder=6,
            )
            texto = eixo.text(
                x_rotulo,
                preco,
                f"  {rotulo}  {self._formatar_y(preco)}",
                va="center",
                ha="left",
                fontsize=8,
                color=cor,
                clip_on=False,
                zorder=8,
            )
            self._artistas.extend([linha, texto])

    def _renderizar_tendencia(self, eixo, desenho: _DesenhoTendencia) -> None:
        cor = CORES.get("aviso", "#D97706")
        linha, = eixo.plot(
            [desenho.x1, desenho.x2],
            [desenho.y1, desenho.y2],
            color=cor,
            linewidth=1.5,
            linestyle="-",
            zorder=7,
        )
        self._artistas.append(linha)

    def _renderizar_horizontal(self, eixo, desenho: _DesenhoHorizontal) -> None:
        cor = CORES.get("primaria", "#2563EB")
        linha = eixo.axhline(
            desenho.y,
            color=cor,
            linewidth=1.2,
            linestyle="--",
            alpha=0.92,
            zorder=6,
        )
        xlim = eixo.get_xlim()
        texto = eixo.text(
            xlim[1],
            desenho.y,
            f"  {self._formatar_y(desenho.y)}",
            va="center",
            ha="left",
            fontsize=8,
            color=cor,
            clip_on=False,
            zorder=8,
        )
        self._artistas.extend([linha, texto])


def restaurar_ferramentas_analise_apos_redesenho(
    canvas: FigureCanvasTkAgg,
    eixo,
    gerenciador_anterior: GerenciadorFerramentasAnaliseGrafico | None,
    *,
    moeda: str = "BRL",
    formatar_rotulo_y: Callable[[float], str] | None = None,
    eixo_volume=None,
) -> GerenciadorFerramentasAnaliseGrafico:
    """Recria o gerenciador no novo canvas preservando desenhos."""
    ferramenta: FerramentaAnalise = "navegar"
    desenhos: list = []
    pendente = None
    if gerenciador_anterior is not None:
        ferramenta, desenhos, pendente = gerenciador_anterior.exportar_estado()

    gerenciador = configurar_ferramentas_analise_grafico(
        canvas,
        eixo,
        moeda=moeda,
        formatar_rotulo_y=formatar_rotulo_y,
    )
    gerenciador.importar_estado(ferramenta, desenhos, pendente)
    canvas._ferramenta_analise_ativa = ferramenta
    if desenhos or pendente:
        gerenciador.reaplicar(eixo)
    reaplicar_marcador_cruz_canvas(canvas, eixo, eixo_volume=eixo_volume)
    return gerenciador


def configurar_ferramentas_analise_grafico(
    canvas: FigureCanvasTkAgg,
    eixo,
    *,
    moeda: str = "BRL",
    formatar_rotulo_y: Callable[[float], str] | None = None,
) -> GerenciadorFerramentasAnaliseGrafico:
    """Cria o gerenciador e liga os eventos de clique no canvas."""
    gerenciador = GerenciadorFerramentasAnaliseGrafico(
        moeda=moeda,
        formatar_rotulo_y=formatar_rotulo_y,
    )
    gerenciador.configurar_eventos(canvas, eixo)
    canvas._gerenciador_ferramentas_analise = gerenciador
    return gerenciador


def montar_ferramentas_analise_grafico(
    pai: ctk.CTkFrame,
    obter_gerenciador: Callable[[], GerenciadorFerramentasAnaliseGrafico | None],
    *,
    rotulo_instrucao: ctk.CTkLabel | None = None,
) -> ctk.CTkFrame:
    """Combo de ferramentas + botao limpar desenhos."""
    frame = ctk.CTkFrame(pai, fg_color="transparent")
    frame.pack(side="left", padx=(16, 0))

    ctk.CTkLabel(
        frame,
        text="Analise",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
    ).pack(side="left", padx=(0, 6))

    rotulos = [nome for _, nome in _FERRAMENTAS_UI]
    mapa_chaves = {nome: chave for chave, nome in _FERRAMENTAS_UI}

    combo = ctk.CTkComboBox(
        frame,
        values=rotulos,
        width=168,
        height=28,
        command=lambda _valor: None,
    )
    combo.set(_FERRAMENTAS_UI[0][1])
    combo.pack(side="left", padx=(0, 8))

    def atualizar_instrucao(chave: FerramentaAnalise) -> None:
        if rotulo_instrucao is None:
            return
        rotulo_instrucao.configure(text=_INSTRUCOES.get(chave, ""))

    def ao_mudar_ferramenta(rotulo: str) -> None:
        gerenciador = obter_gerenciador()
        if gerenciador is None:
            return
        chave = mapa_chaves.get(rotulo, "navegar")
        gerenciador.definir_ferramenta(chave)
        canvas = getattr(gerenciador, "_canvas_ref", None)
        if canvas is not None:
            canvas._ferramenta_analise_ativa = chave
        atualizar_instrucao(chave)

    combo.configure(command=ao_mudar_ferramenta)

    ctk.CTkButton(
        frame,
        text="Limpar desenhos",
        width=118,
        font=ctk.CTkFont(size=12),
        command=lambda: obter_gerenciador().limpar() if obter_gerenciador() else None,
        **estilo_botao_padrao(height=28),
    ).pack(side="left")

    ao_mudar_ferramenta(combo.get())
    return frame


def anexar_ferramentas_analise_ao_grafico(
    canvas: FigureCanvasTkAgg,
    eixo,
    pai_barra: ctk.CTkFrame,
    *,
    moeda: str = "BRL",
    intraday: bool = False,
    rotulo_instrucao: ctk.CTkLabel | None = None,
) -> GerenciadorFerramentasAnaliseGrafico:
    """Configura ferramentas e monta controles na barra do grafico."""
    formatar_y: Callable[[float], str] | None = None
    if moeda:
        formatar_y = lambda valor, _moeda=moeda: formatar_moeda(valor, _moeda)

    gerenciador = configurar_ferramentas_analise_grafico(
        canvas,
        eixo,
        moeda=moeda,
        formatar_rotulo_y=formatar_y,
    )
    canvas._ferramenta_analise_ativa = "navegar"
    montar_ferramentas_analise_grafico(
        pai_barra,
        lambda: gerenciador,
        rotulo_instrucao=rotulo_instrucao,
    )
    return gerenciador
