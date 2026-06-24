"""Provedor primario: Yahoo Finance via biblioteca yfinance."""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from src.Model.cotacao import CotacaoResumo, PontoHistorico, SerieHistorica
from src.Service.mapeamento_periodo import (
    MAPEAMENTO_PERIODO_YFINANCE as MAPEAMENTO_PERIODO,
    dias_do_periodo,
    periodo_usa_janela_em_dias,
)
from src.Tool.registrador_log import RegistradorLog

NOME_PROVEDOR = "Yahoo Finance (yfinance)"


class ProvedorYfinance:
    """Encapsula download de cotacoes e historico pelo yfinance."""

    nome = NOME_PROVEDOR

    def __init__(self) -> None:
        self._log = RegistradorLog()

    def buscar_resumos(self, simbolos: list[str]) -> list[CotacaoResumo]:
        if not simbolos:
            return []

        try:
            dados = yf.download(
                simbolos,
                period="5d",
                group_by="ticker",
                progress=False,
                auto_adjust=True,
            )
        except Exception as exc:
            self._log.aviso(f"{self.nome}: falha no lote de cotacoes: {exc}")
            return []

        resultados: list[CotacaoResumo] = []
        for simbolo in simbolos:
            resumo = self._resumo_de_dataframe(simbolo, self._extrair_serie(simbolo, dados))
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
                dados = yf.download(
                    simbolo,
                    start=data_inicio.date(),
                    end=(data_fim + timedelta(days=1)).date(),
                    interval="1d",
                    progress=False,
                    auto_adjust=True,
                )
                rotulo = "personalizado"
            else:
                cfg = MAPEAMENTO_PERIODO.get(periodo_chave, MAPEAMENTO_PERIODO["mes"])
                if periodo_usa_janela_em_dias(cfg):
                    dias = dias_do_periodo(cfg) or 365 * 3
                    fim = datetime.now()
                    inicio = fim - timedelta(days=dias)
                    dados = yf.download(
                        simbolo,
                        start=inicio.date(),
                        end=(fim + timedelta(days=1)).date(),
                        interval=cfg["interval"],
                        progress=False,
                        auto_adjust=True,
                    )
                else:
                    dados = yf.download(
                        simbolo,
                        period=cfg["period"],
                        interval=cfg["interval"],
                        progress=False,
                        auto_adjust=True,
                    )
                rotulo = periodo_chave

            return self._serie_de_download(simbolo, rotulo, dados)
        except Exception as exc:
            self._log.aviso(f"{self.nome}: historico {simbolo}: {exc}")
            return None

    def _extrair_serie(self, simbolo: str, dados) -> pd.DataFrame | None:
        if dados is None or dados.empty:
            return None

        if isinstance(dados.columns, pd.MultiIndex):
            if simbolo in dados.columns.get_level_values(0):
                return dados[simbolo].dropna(how="all")
            for nivel in ("Ticker", -1):
                try:
                    tickers = dados.columns.get_level_values(nivel)
                    if simbolo in tickers:
                        return dados.xs(simbolo, axis=1, level=nivel).dropna(how="all")
                except (KeyError, ValueError):
                    continue

        if "Close" in dados.columns:
            return dados.dropna(how="all")
        return None

    def _resumo_de_dataframe(self, simbolo: str, serie: pd.DataFrame | None) -> CotacaoResumo | None:
        if serie is None or serie.empty or "Close" not in serie.columns:
            return None

        fechamentos = serie["Close"].dropna()
        if fechamentos.empty:
            return None

        atual = float(fechamentos.iloc[-1])
        anterior = float(fechamentos.iloc[-2]) if len(fechamentos) > 1 else atual
        variacao = atual - anterior
        base = anterior if anterior else 1
        volume = None
        if "Volume" in serie.columns and not serie["Volume"].dropna().empty:
            volume = int(serie["Volume"].dropna().iloc[-1])

        return CotacaoResumo(
            simbolo=simbolo,
            nome=simbolo.replace(".SA", ""),
            preco=round(atual, 2),
            variacao_percentual=round((variacao / base) * 100, 2),
            variacao_valor=round(variacao, 2),
            volume=volume,
            moeda="BRL" if simbolo.endswith(".SA") else "USD",
        )

    def _serie_de_download(self, simbolo: str, rotulo: str, dados) -> SerieHistorica | None:
        serie = self._extrair_serie(simbolo, dados)
        if serie is None and dados is not None and "Close" in getattr(dados, "columns", []):
            serie = dados
        if serie is None or serie.empty or "Close" not in serie.columns:
            return None

        pontos: list[PontoHistorico] = []
        for indice, linha in serie.iterrows():
            if linha["Close"] != linha["Close"]:
                continue
            data_obj = indice.to_pydatetime() if hasattr(indice, "to_pydatetime") else indice
            pontos.append(
                PontoHistorico(
                    data_iso=data_obj.isoformat(),
                    data_exibicao=data_obj.strftime("%d/%m/%Y %H:%M"),
                    preco_fechamento=round(float(linha["Close"]), 2),
                    preco_abertura=round(float(linha["Open"]), 2)
                    if "Open" in linha and linha["Open"] == linha["Open"]
                    else None,
                    preco_maxima=round(float(linha["High"]), 2)
                    if "High" in linha and linha["High"] == linha["High"]
                    else None,
                    preco_minima=round(float(linha["Low"]), 2)
                    if "Low" in linha and linha["Low"] == linha["Low"]
                    else None,
                    volume=int(linha["Volume"])
                    if "Volume" in linha and linha["Volume"] == linha["Volume"]
                    else None,
                )
            )
        if not pontos:
            return None
        return SerieHistorica(simbolo=simbolo, periodo=rotulo, pontos=pontos)
