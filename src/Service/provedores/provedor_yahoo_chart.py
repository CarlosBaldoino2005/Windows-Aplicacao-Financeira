"""Provedor de backup 2: API REST direta do Yahoo Chart (B3 e EUA)."""
from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import quote

from src.Model.cotacao import CotacaoResumo, PontoHistorico, SerieHistorica
from src.Service.mapeamento_periodo import MAPEAMENTO_PERIODO_YAHOO_CHART
from src.Service.provedores.util_provedor import data_para_exibicao, requisicao_json
from src.Tool.registrador_log import RegistradorLog

NOME_PROVEDOR = "Yahoo Chart API"
URL_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{simbolo}"


class ProvedorYahooChart:
    """Consulta query1.finance.yahoo.com quando o yfinance falha."""

    nome = NOME_PROVEDOR

    def __init__(self) -> None:
        self._log = RegistradorLog()

    def buscar_resumos(self, simbolos: list[str]) -> list[CotacaoResumo]:
        resultados: list[CotacaoResumo] = []
        for simbolo in simbolos:
            resumo = self._resumo_por_chart(simbolo, range_param="5d", interval="1d")
            if resumo:
                resultados.append(resumo)
        return resultados

    def buscar_historico(
        self,
        simbolo: str,
        periodo_chave: str,
        data_inicio=None,
        data_fim=None,
    ) -> SerieHistorica | None:
        try:
            if periodo_chave == "personalizado" and data_inicio and data_fim:
                if data_fim < data_inicio:
                    return None
                period1 = int(data_inicio.timestamp())
                period2 = int((data_fim + timedelta(days=1)).timestamp())
                url = (
                    f"{URL_CHART.format(simbolo=quote(simbolo))}"
                    f"?period1={period1}&period2={period2}&interval=1d"
                )
                rotulo = "personalizado"
            else:
                cfg = MAPEAMENTO_PERIODO_YAHOO_CHART.get(
                    periodo_chave, MAPEAMENTO_PERIODO_YAHOO_CHART["mes"]
                )
                url = (
                    f"{URL_CHART.format(simbolo=quote(simbolo))}"
                    f"?range={cfg['range']}&interval={cfg['interval']}"
                )
                rotulo = periodo_chave

            dados = requisicao_json(url, self._log)
            return self._serie_de_chart(simbolo, rotulo, dados)
        except Exception as exc:
            self._log.aviso(f"{self.nome}: historico {simbolo}: {exc}")
            return None

    def buscar_meta(self, simbolo: str) -> dict | None:
        dados = requisicao_json(
            f"{URL_CHART.format(simbolo=quote(simbolo))}?range=5d&interval=1d",
            self._log,
        )
        if not dados:
            return None
        try:
            return dados["chart"]["result"][0]["meta"]
        except (KeyError, IndexError, TypeError):
            return None

    def _resumo_por_chart(self, simbolo: str, range_param: str, interval: str) -> CotacaoResumo | None:
        url = f"{URL_CHART.format(simbolo=quote(simbolo))}?range={range_param}&interval={interval}"
        dados = requisicao_json(url, self._log)
        if not dados:
            return None

        try:
            resultado = dados["chart"]["result"][0]
            meta = resultado["meta"]
            preco = float(meta["regularMarketPrice"])
            anterior = float(meta.get("chartPreviousClose") or meta.get("previousClose") or preco)
            variacao = preco - anterior
            base = anterior if anterior else 1.0
            moeda = str(meta.get("currency") or ("BRL" if simbolo.endswith(".SA") else "USD"))
            nome = str(meta.get("longName") or meta.get("shortName") or simbolo.replace(".SA", ""))
        except (KeyError, IndexError, TypeError, ValueError):
            return None

        return CotacaoResumo(
            simbolo=simbolo,
            nome=nome,
            preco=round(preco, 2),
            variacao_percentual=round((variacao / base) * 100, 2),
            variacao_valor=round(variacao, 2),
            volume=None,
            moeda=moeda,
        )

    def _serie_de_chart(self, simbolo: str, rotulo: str, dados: dict | list | None) -> SerieHistorica | None:
        if not dados or not isinstance(dados, dict):
            return None

        try:
            resultado = dados["chart"]["result"][0]
            timestamps = resultado["timestamp"] or []
            indicadores = resultado["indicators"]["quote"][0]
            aberturas = indicadores.get("open") or []
            fechamentos = indicadores.get("close") or []
            volumes = indicadores.get("volume") or []
        except (KeyError, IndexError, TypeError):
            return None

        pontos: list[PontoHistorico] = []
        for indice, ts in enumerate(timestamps):
            if ts is None:
                continue
            close = fechamentos[indice] if indice < len(fechamentos) else None
            if close is None:
                continue

            data_obj = datetime.fromtimestamp(int(ts))
            abertura = aberturas[indice] if indice < len(aberturas) else None
            volume = volumes[indice] if indice < len(volumes) else None

            pontos.append(
                PontoHistorico(
                    data_iso=data_obj.isoformat(),
                    data_exibicao=data_para_exibicao(data_obj),
                    preco_fechamento=round(float(close), 2),
                    preco_abertura=round(float(abertura), 2) if abertura is not None else None,
                    volume=int(volume) if volume is not None else None,
                )
            )

        if not pontos:
            return None
        return SerieHistorica(simbolo=simbolo, periodo=rotulo, pontos=pontos)
