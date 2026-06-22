"""Busca serie intraday e resumo de um dia passado para a tela Agora."""
from __future__ import annotations

from datetime import date, timedelta

from src.Model.agora_dia_historico import ResumoDiaAgora
from src.Model.cotacao import PontoHistorico, SerieHistorica
from src.Service.provedores.provedor_yahoo_chart import ProvedorYahooChart
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.dia_util_helper import calcular_ultimo_dia_util
from src.Tool.registrador_log import RegistradorLog


class AgoraHistoricoDiaServico:
    """Obtem candles e variacao de um dia especifico via Yahoo Chart."""

    _INTERVALOS = ("1m", "5m", "15m")

    def __init__(self) -> None:
        self._provedor = ProvedorYahooChart()
        self._log = RegistradorLog()

    def buscar_serie_dia(self, simbolo: str, data_ref: date) -> tuple[SerieHistorica | None, str | None]:
        for intervalo in self._INTERVALOS:
            serie = self._provedor.buscar_intraday_em_data(simbolo, data_ref, intervalo)
            if serie and serie.pontos:
                return serie, None
        return None, (
            f"Intraday indisponivel para {codigo_exibicao(simbolo)} em "
            f"{data_ref.strftime('%d/%m/%Y')}."
        )

    def montar_resumo_dia(
        self,
        simbolo: str,
        data_ref: date,
        pontos: list[PontoHistorico],
    ) -> ResumoDiaAgora | None:
        if not pontos:
            return None

        abertura = pontos[0].preco_abertura or pontos[0].preco_fechamento
        fechamento = pontos[-1].preco_fechamento
        maxima = abertura
        minima = abertura
        volume_total = 0
        tem_volume = False

        for ponto in pontos:
            for valor in (ponto.preco_fechamento, ponto.preco_abertura):
                if valor is None:
                    continue
                maxima = max(maxima, valor)
                minima = min(minima, valor)
            if ponto.volume:
                volume_total += int(ponto.volume)
                tem_volume = True

        fechamento_anterior = self._buscar_fechamento_anterior(simbolo, data_ref)
        base = fechamento_anterior if fechamento_anterior and fechamento_anterior > 0 else abertura
        variacao_valor = round(fechamento - base, 4)
        variacao_pct = round((variacao_valor / base) * 100, 2) if base else 0.0
        moeda = "BRL" if simbolo.upper().endswith(".SA") else "USD"

        return ResumoDiaAgora(
            data=data_ref,
            simbolo=simbolo,
            nome=codigo_exibicao(simbolo),
            moeda=moeda,
            abertura=round(float(abertura), 4),
            fechamento=round(float(fechamento), 4),
            maxima=round(float(maxima), 4),
            minima=round(float(minima), 4),
            variacao_valor=round(variacao_valor, 4),
            variacao_pct=variacao_pct,
            fechamento_anterior=fechamento_anterior,
            volume_total=volume_total if tem_volume else None,
        )

    def _buscar_fechamento_anterior(self, simbolo: str, data_ref: date) -> float | None:
        candidato = data_ref - timedelta(days=1)
        for _ in range(10):
            if candidato.weekday() < 5:
                fechamento = self._provedor.buscar_fechamento_diario_em_data(simbolo, candidato)
                if fechamento and fechamento > 0:
                    return fechamento
            candidato -= timedelta(days=1)
        return None


def data_padrao_consulta_agora() -> date:
    """Ultimo dia util (D-1 util) para o campo de data da tela Agora."""
    return calcular_ultimo_dia_util()
