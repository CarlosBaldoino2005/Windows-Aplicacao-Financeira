"""Controles de zoom (+/-) e arraste para mover graficos Matplotlib."""
from __future__ import annotations

from collections.abc import Callable
from typing import TypedDict

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.View.botao_helper import estilo_botao_icone, estilo_botao_padrao
from src.View.tema import CORES

_FATOR_ZOOM = 0.82
_MIN_FRACAO_EIXO_X = 0.04
_MIN_FRACAO_EIXO_Y = 0.08
_LIMIAR_PX_ARRASTE = 6
_FRACAO_ZOOM_PARA_ARRASTE = 0.985


class GestoPan(TypedDict):
    """Estado do arraste (pan) no grafico Matplotlib."""

    ativo: bool
    houve_movimento: bool
    botao: int | None
    xdata: float | None
    ydata: float | None
    xlim: tuple[float, float] | None
    ylim: tuple[float, float] | None
    x_px: int | None
    y_px: int | None


def houve_arraste_pan(canvas: FigureCanvasTkAgg) -> bool:
    """Indica se o ultimo gesto no grafico foi arrastar (e nao um clique simples)."""
    gesto = getattr(canvas, "_gesto_pan", None)
    return bool(gesto and gesto.get("houve_movimento"))


def consumir_arraste_pan(canvas: FigureCanvasTkAgg) -> bool:
    """Retorna True se houve arraste e limpa o flag para o proximo clique."""
    if not houve_arraste_pan(canvas):
        return False
    gesto = getattr(canvas, "_gesto_pan", None)
    if gesto is not None:
        gesto["houve_movimento"] = False
    return True


class ControleZoomGrafico:
    """Aplica zoom e deslocamento no eixo X e Y."""

    def __init__(self, canvas: FigureCanvasTkAgg, eixo) -> None:
        self._canvas = canvas
        self._eixo = eixo
        self._xlim_base: tuple[float, float] | None = None
        self._ylim_base: tuple[float, float] | None = None
        self._ids_eventos: list[tuple[str, int]] = []
        self._gesto: GestoPan = {
            "ativo": False,
            "houve_movimento": False,
            "botao": None,
            "xdata": None,
            "ydata": None,
            "xlim": None,
            "ylim": None,
            "x_px": None,
            "y_px": None,
        }
        self._canvas._gesto_pan = self._gesto

    def registrar_limites_iniciais(self) -> None:
        """Guarda os limites originais apos o primeiro desenho do grafico."""
        self._canvas.draw_idle()
        self._xlim_base = tuple(self._eixo.get_xlim())
        self._ylim_base = tuple(self._eixo.get_ylim())

    def configurar_roda_mouse(self) -> None:
        """Permite ampliar ou reduzir com a roda do mouse sobre o grafico."""
        self._desconectar_por_tipo("scroll")

        def ao_roda(evento) -> None:
            if getattr(evento, "inaxes", None) is not self._eixo:
                return
            if evento.button == "up":
                self.zoom_mais(evento.xdata, evento.ydata)
            elif evento.button == "down":
                self.zoom_menos(evento.xdata, evento.ydata)

        self._ids_eventos.append(("scroll", self._canvas.mpl_connect("scroll_event", ao_roda)))

    def configurar_arrastar(self) -> None:
        """Move o grafico com o mouse: arraste com botao esquerdo (zoom ativo), direito ou meio."""
        self._desconectar_por_tipo("press")
        self._desconectar_por_tipo("motion")
        self._desconectar_por_tipo("release")

        def botao_permite_arraste(botao: int) -> bool:
            if botao in (2, 3):
                return True
            return botao == 1 and self._esta_ampliado()

        def ao_pressionar(evento) -> None:
            if getattr(evento, "inaxes", None) is not self._eixo:
                return
            if not botao_permite_arraste(evento.button):
                return
            self._gesto["ativo"] = True
            self._gesto["houve_movimento"] = False
            self._gesto["botao"] = evento.button
            self._gesto["xdata"] = evento.xdata
            self._gesto["ydata"] = evento.ydata
            self._gesto["xlim"] = tuple(self._eixo.get_xlim())
            self._gesto["ylim"] = tuple(self._eixo.get_ylim())
            self._gesto["x_px"] = evento.x
            self._gesto["y_px"] = evento.y

        def ao_mover(evento) -> None:
            if not self._gesto["ativo"]:
                return
            if evento.xdata is None or evento.ydata is None:
                return
            if self._gesto["x_px"] is not None and self._gesto["y_px"] is not None:
                dist_px = (
                    (evento.x - self._gesto["x_px"]) ** 2 + (evento.y - self._gesto["y_px"]) ** 2
                ) ** 0.5
                if dist_px < _LIMIAR_PX_ARRASTE and not self._gesto["houve_movimento"]:
                    return

            self._gesto["houve_movimento"] = True
            xlim_atual = self._gesto["xlim"]
            ylim_atual = self._gesto["ylim"]
            xdata_inicio = self._gesto["xdata"]
            ydata_inicio = self._gesto["ydata"]
            if (
                xlim_atual is None
                or ylim_atual is None
                or xdata_inicio is None
                or ydata_inicio is None
            ):
                return

            dx = float(xdata_inicio) - float(evento.xdata)
            dy = float(ydata_inicio) - float(evento.ydata)
            self._aplicar_deslocamento(
                xlim_atual[0] + dx,
                xlim_atual[1] + dx,
                ylim_atual[0] + dy,
                ylim_atual[1] + dy,
            )
            self._definir_cursor("fleur")

        def ao_soltar(evento) -> None:
            if self._gesto["ativo"] and evento.button == self._gesto["botao"]:
                self._gesto["ativo"] = False
            self._definir_cursor("")

        self._ids_eventos.append(
            ("press", self._canvas.mpl_connect("button_press_event", ao_pressionar))
        )
        self._ids_eventos.append(
            ("motion", self._canvas.mpl_connect("motion_notify_event", ao_mover))
        )
        self._ids_eventos.append(
            ("release", self._canvas.mpl_connect("button_release_event", ao_soltar))
        )

    def zoom_mais(
        self,
        centro_x: float | None = None,
        centro_y: float | None = None,
    ) -> None:
        self._aplicar_zoom(_FATOR_ZOOM, centro_x, centro_y)

    def zoom_menos(
        self,
        centro_x: float | None = None,
        centro_y: float | None = None,
    ) -> None:
        self._aplicar_zoom(1.0 / _FATOR_ZOOM, centro_x, centro_y)

    def resetar(self) -> None:
        # Import tardio evita dependencia circular com grafico_helper.
        from src.View.grafico_helper import limpar_selecao_periodo_no_grafico
        from src.View.grafico_ferramentas_analise_helper import limpar_ferramentas_analise_no_grafico

        limpar_selecao_periodo_no_grafico(self._canvas)
        limpar_ferramentas_analise_no_grafico(self._canvas)
        if self._xlim_base is None or self._ylim_base is None:
            return
        self._eixo.set_xlim(self._xlim_base)
        self._eixo.set_ylim(self._ylim_base)
        self._canvas.draw_idle()

    def _esta_ampliado(self) -> bool:
        if self._xlim_base is None or self._ylim_base is None:
            return False
        xmin, xmax = self._eixo.get_xlim()
        ymin, ymax = self._eixo.get_ylim()
        span_x = xmax - xmin
        span_y = ymax - ymin
        span_x_base = self._xlim_base[1] - self._xlim_base[0]
        span_y_base = self._ylim_base[1] - self._ylim_base[0]
        if span_x_base <= 0 or span_y_base <= 0:
            return False
        return (
            span_x < span_x_base * _FRACAO_ZOOM_PARA_ARRASTE
            or span_y < span_y_base * _FRACAO_ZOOM_PARA_ARRASTE
        )

    def _definir_cursor(self, cursor: str) -> None:
        try:
            self._canvas.get_tk_widget().configure(cursor=cursor or "")
        except Exception:
            pass

    def _desconectar_por_tipo(self, tipo: str) -> None:
        restantes: list[tuple[str, int]] = []
        for nome, identificador in self._ids_eventos:
            if nome == tipo:
                self._canvas.mpl_disconnect(identificador)
            else:
                restantes.append((nome, identificador))
        self._ids_eventos = restantes

    def _aplicar_deslocamento(
        self,
        xmin: float,
        xmax: float,
        ymin: float,
        ymax: float,
    ) -> None:
        if self._xlim_base is None or self._ylim_base is None:
            return

        span_x = xmax - xmin
        span_y = ymax - ymin

        if xmin < self._xlim_base[0]:
            xmin = self._xlim_base[0]
            xmax = xmin + span_x
        if xmax > self._xlim_base[1]:
            xmax = self._xlim_base[1]
            xmin = xmax - span_x
        if ymin < self._ylim_base[0]:
            ymin = self._ylim_base[0]
            ymax = ymin + span_y
        if ymax > self._ylim_base[1]:
            ymax = self._ylim_base[1]
            ymin = ymax - span_y

        self._eixo.set_xlim(xmin, xmax)
        self._eixo.set_ylim(ymin, ymax)
        self._canvas.draw_idle()

    def _aplicar_zoom(
        self,
        escala: float,
        centro_x: float | None,
        centro_y: float | None,
    ) -> None:
        if self._xlim_base is None or self._ylim_base is None:
            return

        xmin, xmax = self._eixo.get_xlim()
        ymin, ymax = self._eixo.get_ylim()
        cx = centro_x if centro_x is not None else (xmin + xmax) / 2
        cy = centro_y if centro_y is not None else (ymin + ymax) / 2

        metade_x = (xmax - xmin) / 2 * escala
        metade_y = (ymax - ymin) / 2 * escala

        span_x_base = self._xlim_base[1] - self._xlim_base[0]
        span_y_base = self._ylim_base[1] - self._ylim_base[0]
        min_metade_x = max(span_x_base * _MIN_FRACAO_EIXO_X, 0.5)
        min_metade_y = max(span_y_base * _MIN_FRACAO_EIXO_Y, span_y_base * 0.01)
        max_metade_x = span_x_base / 2
        max_metade_y = span_y_base / 2

        metade_x = min(max(metade_x, min_metade_x), max_metade_x)
        metade_y = min(max(metade_y, min_metade_y), max_metade_y)

        novo_xmin = max(self._xlim_base[0], cx - metade_x)
        novo_xmax = min(self._xlim_base[1], cx + metade_x)
        novo_ymin = max(self._ylim_base[0], cy - metade_y)
        novo_ymax = min(self._ylim_base[1], cy + metade_y)

        if novo_xmax - novo_xmin < min_metade_x * 2:
            centro = (novo_xmin + novo_xmax) / 2
            novo_xmin = max(self._xlim_base[0], centro - min_metade_x)
            novo_xmax = min(self._xlim_base[1], centro + min_metade_x)
        if novo_ymax - novo_ymin < min_metade_y * 2:
            centro = (novo_ymin + novo_ymax) / 2
            novo_ymin = max(self._ylim_base[0], centro - min_metade_y)
            novo_ymax = min(self._ylim_base[1], centro + min_metade_y)

        self._eixo.set_xlim(novo_xmin, novo_xmax)
        self._eixo.set_ylim(novo_ymin, novo_ymax)
        self._canvas.draw_idle()


def criar_controle_zoom(canvas: FigureCanvasTkAgg, eixo) -> ControleZoomGrafico:
    """Cria zoom, roda do mouse e arraste para mover o grafico."""
    controle = ControleZoomGrafico(canvas, eixo)
    controle.registrar_limites_iniciais()
    controle.configurar_roda_mouse()
    controle.configurar_arrastar()
    return controle


def montar_botoes_zoom_grafico(
    pai: ctk.CTkFrame,
    obter_controle: Callable[[], ControleZoomGrafico | None],
) -> ctk.CTkFrame:
    """Monta botoes - / + / Reset na barra informada."""

    def executar(acao: str) -> None:
        controle = obter_controle()
        if controle is None:
            return
        if acao == "mais":
            controle.zoom_mais()
        elif acao == "menos":
            controle.zoom_menos()
        else:
            controle.resetar()

    frame = ctk.CTkFrame(pai, fg_color="transparent")
    frame.pack(side="left")

    ctk.CTkLabel(
        frame,
        text="Zoom",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
    ).pack(side="left", padx=(0, 6))

    ctk.CTkButton(
        frame,
        text="−",
        width=34,
        height=28,
        font=ctk.CTkFont(size=16, weight="bold"),
        command=lambda: executar("menos"),
        **estilo_botao_icone(),
    ).pack(side="left", padx=(0, 4))

    ctk.CTkButton(
        frame,
        text="+",
        width=34,
        height=28,
        font=ctk.CTkFont(size=16, weight="bold"),
        command=lambda: executar("mais"),
        **estilo_botao_icone(),
    ).pack(side="left", padx=(0, 8))

    ctk.CTkButton(
        frame,
        text="Reset",
        width=64,
        font=ctk.CTkFont(size=12),
        command=lambda: executar("reset"),
        **estilo_botao_padrao(height=28),
    ).pack(side="left")

    ctk.CTkLabel(
        frame,
        text="Arraste o grafico com o mouse apos ampliar",
        font=ctk.CTkFont(size=11),
        text_color=CORES["textoSecundario"],
    ).pack(side="left", padx=(12, 0))

    return frame
