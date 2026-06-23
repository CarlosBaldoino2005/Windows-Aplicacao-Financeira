"""Busca OHLCV diario dos ultimos trinta pregões para a tela Agora."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import date, datetime

import yfinance as yf

from src.Model.resumo_semana_agora import DiaResumoSemanaAgora, ResumoSemanaAgora
from src.Service.agora_historico_dia_servico import AgoraHistoricoDiaServico
from src.Service.provedores.provedor_yahoo_chart import URL_CHART
from src.Service.provedores.util_provedor import eh_acao_b3, requisicao_json
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.dia_util_helper import eh_dia_util
from src.Tool.horario_extremo_intraday_helper import obter_horarios_alta_baixa_intraday
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import normalizar_simbolo, normalizar_simbolo_cripto

_QUANTIDADE_DIAS_UTEIS = 30
_PARALELO_HORARIOS = 8


@dataclass(frozen=True)
class _CandleDiario:
    data: date
    abertura: float
    maxima: float
    minima: float
    fechamento: float
    volume: int | None


class ResumoSemanaAgoraServico:
    """Monta metricas dos ultimos trinta dias uteis (ou pregões) do ativo."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._historico_dia = AgoraHistoricoDiaServico()

    def obter_resumo(self, simbolo: str) -> tuple[ResumoSemanaAgora | None, str | None]:
        simbolo_ok = self._resolver_simbolo(simbolo)
        if not simbolo_ok:
            return None, "Simbolo invalido."

        candles = self._buscar_candles_diarios(simbolo_ok)
        if not candles:
            return None, (
                f"Nao foi possivel carregar o historico diario de {codigo_exibicao(simbolo_ok)}."
            )

        candles_filtrados = self._filtrar_pregoes(candles, simbolo_ok)
        if len(candles_filtrados) < _QUANTIDADE_DIAS_UTEIS:
            return None, (
                f"Dados insuficientes: apenas {len(candles_filtrados)} pregão(ões) "
                f"disponiveis para {codigo_exibicao(simbolo_ok)}."
            )

        inicio_global = len(candles_filtrados) - _QUANTIDADE_DIAS_UTEIS
        ultimos = candles_filtrados[inicio_global:]
        moeda = self._moeda_padrao(simbolo_ok)
        dias: list[DiaResumoSemanaAgora] = []

        for indice, candle in enumerate(ultimos):
            fechamento_anterior = None
            indice_global = inicio_global + indice
            if indice_global > 0:
                fechamento_anterior = candles_filtrados[indice_global - 1].fechamento

            base = (
                fechamento_anterior
                if fechamento_anterior is not None and fechamento_anterior > 0
                else candle.abertura
            )
            variacao_valor = round(candle.fechamento - base, 4)
            variacao_pct = round((variacao_valor / base) * 100, 2) if base else 0.0
            amplitude_valor = round(candle.maxima - candle.minima, 4)
            base_amplitude = candle.minima if candle.minima > 0 else candle.abertura
            amplitude_pct = (
                round((amplitude_valor / base_amplitude) * 100, 2) if base_amplitude > 0 else 0.0
            )

            dias.append(
                DiaResumoSemanaAgora(
                    data=candle.data,
                    abertura=round(candle.abertura, 4),
                    maxima=round(candle.maxima, 4),
                    minima=round(candle.minima, 4),
                    fechamento=round(candle.fechamento, 4),
                    variacao_valor=variacao_valor,
                    variacao_pct=variacao_pct,
                    amplitude_valor=amplitude_valor,
                    amplitude_pct=amplitude_pct,
                    fechamento_anterior=(
                        round(fechamento_anterior, 4) if fechamento_anterior is not None else None
                    ),
                    volume=candle.volume,
                )
            )

        dias = self._enriquecer_horarios_extremos(simbolo_ok, dias)

        fechamentos = [dia.fechamento for dia in dias]
        media_fechamento = round(sum(fechamentos) / len(fechamentos), 4)
        volumes = [dia.volume for dia in dias if dia.volume is not None]
        volume_total = sum(volumes) if volumes else None

        referencia_anterior = dias[0].fechamento_anterior
        ultimo_fechamento = dias[-1].fechamento
        variacao_acumulada_valor = None
        variacao_acumulada_pct = None
        if referencia_anterior is not None and referencia_anterior > 0:
            variacao_acumulada_valor = round(ultimo_fechamento - referencia_anterior, 4)
            variacao_acumulada_pct = round(
                ((ultimo_fechamento / referencia_anterior) - 1) * 100,
                2,
            )

        return (
            ResumoSemanaAgora(
                simbolo=simbolo_ok,
                nome=codigo_exibicao(simbolo_ok),
                moeda=moeda,
                dias=tuple(dias),
                variacao_acumulada_valor=variacao_acumulada_valor,
                variacao_acumulada_pct=variacao_acumulada_pct,
                media_fechamento=media_fechamento,
                volume_total=volume_total,
            ),
            None,
        )

    def _enriquecer_horarios_extremos(
        self,
        simbolo: str,
        dias: list[DiaResumoSemanaAgora],
    ) -> list[DiaResumoSemanaAgora]:
        """Busca intraday de cada dia em paralelo para obter horario da alta e da baixa."""

        def buscar_horarios(dia: DiaResumoSemanaAgora) -> DiaResumoSemanaAgora:
            serie, _ = self._historico_dia.buscar_serie_dia(simbolo, dia.data)
            if serie is None or not serie.pontos:
                return dia
            horario_alta, horario_baixa = obter_horarios_alta_baixa_intraday(
                serie.pontos,
                preco_alta=dia.maxima,
                preco_baixa=dia.minima,
            )
            return replace(dia, horario_alta=horario_alta, horario_baixa=horario_baixa)

        with ThreadPoolExecutor(max_workers=_PARALELO_HORARIOS) as executor:
            return list(executor.map(buscar_horarios, dias))

    def _buscar_candles_diarios(self, simbolo: str) -> list[_CandleDiario]:
        candles = self._candles_yfinance(simbolo)
        if candles:
            return candles
        return self._candles_yahoo_chart(simbolo)

    def _candles_yfinance(self, simbolo: str) -> list[_CandleDiario]:
        try:
            historico = yf.Ticker(simbolo).history(period="3mo", interval="1d")
        except Exception as exc:
            self._log.aviso(f"Yahoo Finance (resumo do mes) falhou para {simbolo}: {exc}")
            return []

        if historico is None or historico.empty:
            return []

        candles: list[_CandleDiario] = []
        for indice, linha in historico.iterrows():
            data_ref = self._data_do_indice(indice)
            if data_ref is None:
                continue
            try:
                abertura = float(linha["Open"])
                maxima = float(linha["High"])
                minima = float(linha["Low"])
                fechamento = float(linha["Close"])
            except (TypeError, ValueError, KeyError):
                continue
            if fechamento <= 0:
                continue

            volume_bruto = linha.get("Volume")
            volume = None
            if volume_bruto is not None:
                try:
                    volume = int(float(volume_bruto))
                except (TypeError, ValueError):
                    volume = None

            candles.append(
                _CandleDiario(
                    data=data_ref,
                    abertura=abertura,
                    maxima=maxima,
                    minima=minima,
                    fechamento=fechamento,
                    volume=volume,
                )
            )

        candles.sort(key=lambda item: item.data)
        return candles

    def _candles_yahoo_chart(self, simbolo: str) -> list[_CandleDiario]:
        from urllib.parse import quote

        url = f"{URL_CHART.format(simbolo=quote(simbolo))}?range=3mo&interval=1d"
        dados = requisicao_json(url, self._log)
        if not dados or not isinstance(dados, dict):
            return []

        try:
            resultado = dados["chart"]["result"][0]
            timestamps = resultado["timestamp"] or []
            indicadores = resultado["indicators"]["quote"][0]
            aberturas = indicadores.get("open") or []
            maximas = indicadores.get("high") or []
            minimas = indicadores.get("low") or []
            fechamentos = indicadores.get("close") or []
            volumes = indicadores.get("volume") or []
        except (KeyError, IndexError, TypeError):
            return []

        candles: list[_CandleDiario] = []
        for indice, ts in enumerate(timestamps):
            if ts is None:
                continue
            fechamento = fechamentos[indice] if indice < len(fechamentos) else None
            if fechamento is None:
                continue
            try:
                abertura = float(aberturas[indice]) if indice < len(aberturas) else float(fechamento)
                maxima = float(maximas[indice]) if indice < len(maximas) else float(fechamento)
                minima = float(minimas[indice]) if indice < len(minimas) else float(fechamento)
                fechamento_f = float(fechamento)
            except (TypeError, ValueError):
                continue
            if fechamento_f <= 0:
                continue

            volume = None
            if indice < len(volumes) and volumes[indice] is not None:
                try:
                    volume = int(float(volumes[indice]))
                except (TypeError, ValueError):
                    volume = None

            data_ref = datetime.fromtimestamp(int(ts)).date()
            candles.append(
                _CandleDiario(
                    data=data_ref,
                    abertura=abertura,
                    maxima=maxima,
                    minima=minima,
                    fechamento=fechamento_f,
                    volume=volume,
                )
            )

        candles.sort(key=lambda item: item.data)
        return candles

    @staticmethod
    def _filtrar_pregoes(candles: list[_CandleDiario], simbolo: str) -> list[_CandleDiario]:
        if simbolo.endswith("-USD"):
            return candles
        if eh_acao_b3(simbolo) or simbolo.endswith(".SA"):
            return [candle for candle in candles if eh_dia_util(candle.data)]
        return [candle for candle in candles if eh_dia_util(candle.data)]

    @staticmethod
    def _data_do_indice(indice) -> date | None:
        try:
            if hasattr(indice, "date"):
                return indice.date()
            if hasattr(indice, "to_pydatetime"):
                return indice.to_pydatetime().date()
        except Exception:
            return None
        return None

    @staticmethod
    def _moeda_padrao(simbolo: str) -> str:
        if simbolo.endswith(".SA"):
            return "BRL"
        return "USD"

    @staticmethod
    def _resolver_simbolo(simbolo: str) -> str:
        texto = (simbolo or "").strip().upper()
        if not texto:
            return ""

        if texto.startswith("^") or texto.endswith("-USD"):
            return texto

        simbolo_acao, erro_acao = normalizar_simbolo(texto)
        if simbolo_acao and not erro_acao:
            return simbolo_acao

        simbolo_cripto, erro_cripto = normalizar_simbolo_cripto(texto)
        if simbolo_cripto and not erro_cripto:
            return simbolo_cripto

        return texto
