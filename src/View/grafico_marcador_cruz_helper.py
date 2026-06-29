"""Marcador de cruz (linhas H/V) ao clicar com o botao do meio do mouse no grafico."""
from __future__ import annotations

from dataclasses import dataclass

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.View.tema import CORES


@dataclass
class _EstadoMarcadorCruz:
    x: float | None = None
    y_preco: float | None = None
    y_volume: float | None = None


class GerenciadorMarcadorCruzScroll:
    """Linhas horizontal e vertical fixas no ponto do clique com o scroll (botao do meio)."""

    def __init__(
        self,
        canvas: FigureCanvasTkAgg,
        eixo,
        *,
        eixo_volume=None,
    ) -> None:
        self._canvas = canvas
        self._eixo = eixo
        self._eixo_volume = eixo_volume
        self._estado = _carregar_estado_da_figura(eixo)
        self._artistas: list = []
        self._cid_evento: int | None = None

    def _figura(self):
        return self._eixo.figure

    def _persistir_estado(self) -> None:
        setattr(self._figura(), "_marcador_cruz_estado", self._estado)

    def atualizar_eixos(self, eixo, *, eixo_volume=None) -> None:
        self._eixo = eixo
        if eixo_volume is not None:
            self._eixo_volume = eixo_volume

    def configurar_eventos(self) -> None:
        self._desconectar_eventos()

        def ao_soltar(evento) -> None:
            from src.View.grafico_zoom_helper import houve_arraste_pan

            if evento.button != 2:
                return
            if houve_arraste_pan(self._canvas):
                return

            eixos_validos = [self._eixo]
            if self._eixo_volume is not None:
                eixos_validos.append(self._eixo_volume)
            if getattr(evento, "inaxes", None) not in eixos_validos:
                return
            if evento.xdata is None:
                return

            self._estado.x = float(evento.xdata)
            if evento.inaxes == self._eixo:
                self._estado.y_preco = (
                    float(evento.ydata) if evento.ydata is not None else None
                )
                self._estado.y_volume = None
            elif self._eixo_volume is not None and evento.inaxes == self._eixo_volume:
                self._estado.y_volume = (
                    float(evento.ydata) if evento.ydata is not None else None
                )
                self._estado.y_preco = None

            self._persistir_estado()
            self.reaplicar()
            self._canvas.draw_idle()

        self._cid_evento = self._canvas.mpl_connect("button_release_event", ao_soltar)

    def reaplicar(self) -> None:
        self._remover_artistas()
        if self._estado.x is None:
            return

        cor = CORES.get("textoSecundario", "#64748B")
        estilo = {
            "color": cor,
            "linewidth": 1.2,
            "linestyle": "-",
            "alpha": 0.9,
            "zorder": 7,
        }

        self._artistas.append(self._eixo.axvline(self._estado.x, **estilo))
        if self._estado.y_preco is not None:
            self._artistas.append(self._eixo.axhline(self._estado.y_preco, **estilo))

        if self._eixo_volume is not None:
            self._artistas.append(self._eixo_volume.axvline(self._estado.x, **estilo))
            if self._estado.y_volume is not None:
                self._artistas.append(self._eixo_volume.axhline(self._estado.y_volume, **estilo))

    def _remover_artistas(self) -> None:
        for artista in self._artistas:
            try:
                artista.remove()
            except Exception:
                pass
        self._artistas.clear()

    def _desconectar_eventos(self) -> None:
        if self._cid_evento is None:
            return
        try:
            self._canvas.mpl_disconnect(self._cid_evento)
        except Exception:
            pass
        self._cid_evento = None


def _carregar_estado_da_figura(eixo) -> _EstadoMarcadorCruz:
    salvo = getattr(eixo.figure, "_marcador_cruz_estado", None)
    if isinstance(salvo, _EstadoMarcadorCruz):
        return _EstadoMarcadorCruz(
            x=salvo.x,
            y_preco=salvo.y_preco,
            y_volume=salvo.y_volume,
        )
    return _EstadoMarcadorCruz()


def configurar_marcador_cruz_scroll(
    canvas: FigureCanvasTkAgg,
    eixo,
    *,
    eixo_volume=None,
) -> GerenciadorMarcadorCruzScroll:
    """Registra clique do botao do meio para marcar cruz H/V no grafico."""
    gerenciador = getattr(canvas, "_marcador_cruz_scroll", None)
    if gerenciador is None:
        gerenciador = GerenciadorMarcadorCruzScroll(canvas, eixo, eixo_volume=eixo_volume)
        canvas._marcador_cruz_scroll = gerenciador
    else:
        gerenciador.atualizar_eixos(eixo, eixo_volume=eixo_volume)
        gerenciador._estado = _carregar_estado_da_figura(eixo)

    gerenciador.configurar_eventos()
    gerenciador.reaplicar()
    return gerenciador


def reaplicar_marcador_cruz_canvas(
    canvas: FigureCanvasTkAgg | None,
    eixo,
    *,
    eixo_volume=None,
) -> None:
    """Recria as linhas apos redesenhar o grafico (preserva o ultimo ponto marcado)."""
    if canvas is None:
        return
    gerenciador = getattr(canvas, "_marcador_cruz_scroll", None)
    if gerenciador is None:
        gerenciador = configurar_marcador_cruz_scroll(canvas, eixo, eixo_volume=eixo_volume)
    else:
        gerenciador.atualizar_eixos(eixo, eixo_volume=eixo_volume)
        gerenciador._estado = _carregar_estado_da_figura(eixo)
        gerenciador.reaplicar()
