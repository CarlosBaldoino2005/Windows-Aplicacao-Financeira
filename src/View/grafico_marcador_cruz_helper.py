"""Marcador de cruz (linhas H/V) ao clicar com o botao do meio do mouse no grafico."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.transforms import blended_transform_factory

from src.View.formatadores import formatar_moeda
from src.View.tema import CORES


@dataclass
class _EstadoMarcadorCruz:
    x: float | None = None
    y_preco: float | None = None
    y_volume: float | None = None


@dataclass
class _ContextoMarcadorCruz:
    moeda: str = "BRL"
    intraday: bool = False
    pontos: list[dict] | None = None


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
        estilo_texto = {
            "fontsize": 8,
            "color": cor,
            "clip_on": False,
            "zorder": 8,
        }

        self._artistas.append(self._eixo.axvline(self._estado.x, **estilo))
        if self._estado.y_preco is not None:
            self._artistas.append(self._eixo.axhline(self._estado.y_preco, **estilo))

        if self._eixo_volume is not None:
            self._artistas.append(self._eixo_volume.axvline(self._estado.x, **estilo))
            if self._estado.y_volume is not None:
                self._artistas.append(self._eixo_volume.axhline(self._estado.y_volume, **estilo))

        contexto = _obter_contexto(self._figura())
        self._adicionar_rotulos_valor(contexto, cor, estilo_texto)

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

    def _adicionar_rotulos_valor(
        self,
        contexto: _ContextoMarcadorCruz,
        cor: str,
        estilo_texto: dict,
    ) -> None:
        rotulo_x = _formatar_rotulo_x_marcador(self._estado.x, contexto)
        eixo_horario = self._eixo_volume if self._eixo_volume is not None else self._eixo
        trans_horario = blended_transform_factory(eixo_horario.transData, eixo_horario.transAxes)
        self._artistas.append(
            eixo_horario.text(
                self._estado.x,
                -0.06,
                rotulo_x,
                transform=trans_horario,
                ha="center",
                va="top",
                **estilo_texto,
            )
        )

        if self._estado.y_preco is not None:
            xlim = self._eixo.get_xlim()
            texto_preco = formatar_moeda(self._estado.y_preco, contexto.moeda)
            self._artistas.append(
                self._eixo.text(
                    xlim[1],
                    self._estado.y_preco,
                    f"  {texto_preco}",
                    va="center",
                    ha="left",
                    **estilo_texto,
                )
            )

        if self._eixo_volume is not None and self._estado.y_volume is not None:
            xlim_vol = self._eixo_volume.get_xlim()
            texto_volume = _formatar_volume_marcador(int(round(self._estado.y_volume)))
            self._artistas.append(
                self._eixo_volume.text(
                    xlim_vol[1],
                    self._estado.y_volume,
                    f"  Vol. {texto_volume}",
                    va="center",
                    ha="left",
                    **estilo_texto,
                )
            )


def _obter_contexto(figura) -> _ContextoMarcadorCruz:
    salvo = getattr(figura, "_marcador_cruz_contexto", None)
    if isinstance(salvo, _ContextoMarcadorCruz):
        return salvo
    return _ContextoMarcadorCruz()


def _mesclar_contexto(
    figura,
    *,
    moeda: str | None = None,
    intraday: bool | None = None,
    pontos: list[dict] | None = None,
) -> _ContextoMarcadorCruz:
    contexto = _obter_contexto(figura)
    if moeda is not None:
        contexto.moeda = moeda
    if intraday is not None:
        contexto.intraday = intraday
    if pontos is not None:
        contexto.pontos = pontos
    setattr(figura, "_marcador_cruz_contexto", contexto)
    return contexto


def _formatar_volume_marcador(volume: int) -> str:
    return f"{int(volume):,}".replace(",", ".")


def _minutos_dia_para_horario(minutos: float) -> str:
    total = max(0, int(round(minutos)))
    hora = (total // 60) % 24
    minuto = total % 60
    return f"{hora:02d}:{minuto:02d}"


def _formatar_rotulo_x_marcador(x: float, contexto: _ContextoMarcadorCruz) -> str:
    if contexto.intraday:
        return _minutos_dia_para_horario(x)
    if contexto.pontos:
        from src.View.grafico_helper import _formatar_rotulo_data_eixo

        indices = np.arange(len(contexto.pontos), dtype=float)
        if len(indices) == 0:
            return "—"
        indice = int(np.argmin(np.abs(indices - x)))
        ponto = contexto.pontos[indice]
        return _formatar_rotulo_data_eixo(str(ponto.get("data", "")))
    return f"{x:.2f}"


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
    moeda: str | None = None,
    intraday: bool | None = None,
    pontos: list[dict] | None = None,
) -> GerenciadorMarcadorCruzScroll:
    """Registra clique do botao do meio para marcar cruz H/V no grafico."""
    _mesclar_contexto(
        eixo.figure,
        moeda=moeda,
        intraday=intraday,
        pontos=pontos,
    )
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
