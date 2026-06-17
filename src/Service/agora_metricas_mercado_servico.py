"""Metricas de mercado para o painel da tela Agora."""
from __future__ import annotations

from dataclasses import dataclass

import yfinance as yf

from src.Service.provedores.provedor_brapi import ProvedorBrapi
from src.Service.provedores.provedor_yahoo_chart import ProvedorYahooChart
from src.Service.provedores.util_provedor import eh_acao_b3
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import normalizar_simbolo, normalizar_simbolo_cripto
from src.View.formatadores import formatar_moeda, formatar_numero_grande


@dataclass(frozen=True)
class MetricasMercadoAgora:
    """Valores formatados para exibicao no painel de metricas."""

    abertura: str = "—"
    alta_dia: str = "—"
    baixa_dia: str = "—"
    volume_medio: str = "—"
    volume_dia: str = "—"
    alta_52_semanas: str = "—"
    baixa_52_semanas: str = "—"
    circulacao: str = "—"
    rotulo_circulacao: str = "Acoes em circulacao"
    resumo: str = ""


class AgoraMetricasMercadoServico:
    """Busca abertura, faixa do dia, volume e dados de 52 semanas."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._brapi = ProvedorBrapi()
        self._yahoo_chart = ProvedorYahooChart()

    def obter_metricas(self, simbolo: str) -> MetricasMercadoAgora:
        simbolo_ok = self._resolver_simbolo(simbolo)
        if not simbolo_ok:
            return MetricasMercadoAgora()

        metricas = self._tentar_yfinance(simbolo_ok)
        if metricas is not None and self._metricas_tem_dados(metricas):
            return metricas

        metricas_brapi = None
        if eh_acao_b3(simbolo_ok):
            metricas_brapi = self._tentar_brapi(simbolo_ok)
            if metricas_brapi is not None and self._metricas_tem_dados(metricas_brapi):
                return metricas_brapi

        metricas_chart = self._tentar_yahoo_chart(simbolo_ok)
        if metricas_chart is not None and self._metricas_tem_dados(metricas_chart):
            return metricas_chart

        return metricas or metricas_brapi or MetricasMercadoAgora()

    @staticmethod
    def _resolver_simbolo(simbolo: str) -> str:
        """Garante sufixo .SA para acoes B3 e -USD para cripto."""
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

    @staticmethod
    def _info_tem_dados_mercado(info: dict) -> bool:
        if not info:
            return False
        chaves = (
            "regularMarketOpen",
            "regularMarketDayHigh",
            "regularMarketDayLow",
            "regularMarketPrice",
            "currentPrice",
            "fiftyTwoWeekHigh",
            "regularMarketVolume",
            "volume24Hr",
        )
        return any(info.get(chave) is not None for chave in chaves)

    @staticmethod
    def _metricas_tem_dados(metricas: MetricasMercadoAgora) -> bool:
        campos = (
            metricas.abertura,
            metricas.alta_dia,
            metricas.baixa_dia,
            metricas.volume_medio,
            metricas.volume_dia,
            metricas.alta_52_semanas,
            metricas.baixa_52_semanas,
            metricas.circulacao,
        )
        return any(valor != "—" for valor in campos)

    def _tentar_yfinance(self, simbolo: str) -> MetricasMercadoAgora | None:
        try:
            info = yf.Ticker(simbolo).info or {}
        except Exception as exc:
            self._log.aviso(f"Yahoo Finance (metricas Agora) falhou para {simbolo}: {exc}")
            return None

        if not info:
            return None

        if not self._info_tem_dados_mercado(info):
            return None

        moeda = self._moeda_de_info(simbolo, info)
        eh_cripto = simbolo.endswith("-USD")
        resumo = str(
            info.get("longBusinessSummary")
            or info.get("description")
            or info.get("longName")
            or ""
        ).strip()

        return MetricasMercadoAgora(
            abertura=self._formatar_preco(info.get("regularMarketOpen"), moeda),
            alta_dia=self._formatar_preco(
                info.get("regularMarketDayHigh") or info.get("dayHigh"),
                moeda,
            ),
            baixa_dia=self._formatar_preco(
                info.get("regularMarketDayLow") or info.get("dayLow"),
                moeda,
            ),
            volume_medio=self._formatar_volume(
                info.get("averageVolume") or info.get("averageVolume10days"),
                moeda,
            ),
            volume_dia=self._formatar_volume(
                info.get("regularMarketVolume") or info.get("volume24Hr"),
                moeda,
            ),
            alta_52_semanas=self._formatar_preco(info.get("fiftyTwoWeekHigh"), moeda),
            baixa_52_semanas=self._formatar_preco(info.get("fiftyTwoWeekLow"), moeda),
            circulacao=self._formatar_circulacao(info, eh_cripto=eh_cripto),
            rotulo_circulacao=(
                "Oferta em circulacao" if eh_cripto else "Acoes em circulacao"
            ),
            resumo=resumo,
        )

    def _tentar_brapi(self, simbolo: str) -> MetricasMercadoAgora | None:
        dados = self._brapi.buscar_cotacao_detalhe(simbolo)
        if not dados or not dados.get("results"):
            return None

        item = dados["results"][0]
        moeda = str(item.get("currency") or "BRL")
        return MetricasMercadoAgora(
            abertura=self._formatar_preco(item.get("regularMarketOpen"), moeda),
            alta_dia=self._formatar_preco(item.get("regularMarketDayHigh"), moeda),
            baixa_dia=self._formatar_preco(item.get("regularMarketDayLow"), moeda),
            volume_medio=self._formatar_volume(item.get("averageDailyVolume3Month"), moeda),
            volume_dia=self._formatar_volume(item.get("regularMarketVolume"), moeda),
            alta_52_semanas=self._formatar_preco(item.get("fiftyTwoWeekHigh"), moeda),
            baixa_52_semanas=self._formatar_preco(item.get("fiftyTwoWeekLow"), moeda),
            circulacao=self._formatar_circulacao(item, eh_cripto=False),
            resumo=str(item.get("longName") or item.get("shortName") or "").strip(),
        )

    def _tentar_yahoo_chart(self, simbolo: str) -> MetricasMercadoAgora | None:
        meta = self._yahoo_chart.buscar_meta(simbolo)
        if not meta or not self._info_tem_dados_mercado(meta):
            return None

        moeda = "BRL" if simbolo.endswith(".SA") else str(meta.get("currency") or "USD")
        eh_cripto = simbolo.endswith("-USD")
        resumo = str(meta.get("longName") or meta.get("shortName") or "").strip()

        return MetricasMercadoAgora(
            abertura=self._formatar_preco(
                meta.get("regularMarketOpen") or meta.get("chartPreviousClose"),
                moeda,
            ),
            alta_dia=self._formatar_preco(meta.get("regularMarketDayHigh"), moeda),
            baixa_dia=self._formatar_preco(meta.get("regularMarketDayLow"), moeda),
            volume_medio="—",
            volume_dia=self._formatar_volume(meta.get("regularMarketVolume"), moeda),
            alta_52_semanas=self._formatar_preco(meta.get("fiftyTwoWeekHigh"), moeda),
            baixa_52_semanas=self._formatar_preco(meta.get("fiftyTwoWeekLow"), moeda),
            circulacao="—",
            rotulo_circulacao=(
                "Oferta em circulacao" if eh_cripto else "Acoes em circulacao"
            ),
            resumo=resumo,
        )

    @staticmethod
    def _moeda_de_info(simbolo: str, info: dict) -> str:
        if simbolo.endswith(".SA"):
            return "BRL"
        return str(info.get("currency") or "USD")

    @staticmethod
    def _formatar_preco(valor, moeda: str) -> str:
        if valor is None or valor == "":
            return "—"
        try:
            return formatar_moeda(float(valor), moeda)
        except (TypeError, ValueError):
            return "—"

    @staticmethod
    def _formatar_volume(valor, moeda: str) -> str:
        if valor is None or valor == "":
            return "—"
        try:
            return formatar_numero_grande(float(valor), moeda)
        except (TypeError, ValueError):
            return "—"

    @staticmethod
    def _formatar_circulacao(info: dict, *, eh_cripto: bool) -> str:
        chave = "circulatingSupply" if eh_cripto else "sharesOutstanding"
        valor = info.get(chave)
        if valor is None or valor == "":
            return "—"
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return "—"
        if eh_cripto:
            return formatar_numero_grande(numero, "USD")
        return f"{int(numero):,}".replace(",", ".")
