"""Busca cotacoes e historico via yfinance (dados publicos, sem API key)."""
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from src.Model.acoes_universo import ACOES_MONITORADAS, ACOES_PADRAO, LIMITE_ACOES_PAINEL
from src.Model.cotacao import CotacaoResumo, PontoHistorico, SerieHistorica
from src.Tool.registrador_log import RegistradorLog

MAPEAMENTO_PERIODO = {
    "dia": {"period": "1d", "interval": "5m"},
    "semana": {"period": "5d", "interval": "30m"},
    "mes": {"period": "1mo", "interval": "1d"},
    "trimestre": {"period": "3mo", "interval": "1d"},
    "semestre": {"period": "6mo", "interval": "1d"},
    "ano": {"period": "1y", "interval": "1d"},
}


class MercadoServico:
    """Regras de negocio para consulta ao mercado."""

    def __init__(self) -> None:
        self._log = RegistradorLog()

    def listar_acoes_padrao(self) -> list[str]:
        return self.listar_acoes_monitoradas()

    def listar_acoes_monitoradas(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[str]:
        from src.Model.acoes_universo import montar_lista_monitoradas

        return montar_lista_monitoradas(quantidade)

    def _extrair_serie_simbolo(self, dados, simbolo: str):
        """
        Extrai DataFrame OHLCV de um simbolo.
        yfinance 1.4+ usa formatos diferentes para 1 ou varios tickers.
        """
        if dados is None or dados.empty:
            return None

        if isinstance(dados.columns, pd.MultiIndex):
            # Varias acoes: nivel 0 = ticker (group_by=ticker).
            if simbolo in dados.columns.get_level_values(0):
                return dados[simbolo].dropna(how="all")

            # Uma acao: nivel Ticker ou ultimo nivel = codigo (ex. VALE3.SA).
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

    def buscar_resumos(self, simbolos: list[str]) -> list[CotacaoResumo]:
        """Obtem resumo de varias acoes (em lotes para listas grandes)."""
        if not simbolos:
            return []

        tamanho_lote = 25
        if len(simbolos) <= tamanho_lote:
            return self._buscar_resumos_lote(simbolos)

        agregado: list[CotacaoResumo] = []
        for inicio in range(0, len(simbolos), tamanho_lote):
            lote = simbolos[inicio : inicio + tamanho_lote]
            agregado.extend(self._buscar_resumos_lote(lote))
        return agregado

    def _buscar_resumos_lote(self, simbolos: list[str]) -> list[CotacaoResumo]:
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
            self._log.erro(f"Download cotacoes: {exc}")
            return []

        resultados: list[CotacaoResumo] = []
        for simbolo in simbolos:
            try:
                serie = self._extrair_serie_simbolo(dados, simbolo)
                if serie is None or serie.empty or "Close" not in serie.columns:
                    continue

                fechamentos = serie["Close"].dropna()
                if fechamentos.empty:
                    continue

                fechamento_atual = float(fechamentos.iloc[-1])
                fechamento_anterior = (
                    float(fechamentos.iloc[-2]) if len(fechamentos) > 1 else fechamento_atual
                )
                variacao_valor = fechamento_atual - fechamento_anterior
                base = fechamento_anterior if fechamento_anterior else 1
                variacao_pct = (variacao_valor / base) * 100

                moeda = "BRL" if simbolo.endswith(".SA") else "USD"
                volume = None
                if "Volume" in serie.columns and not serie["Volume"].dropna().empty:
                    volume = int(serie["Volume"].dropna().iloc[-1])

                resultados.append(
                    CotacaoResumo(
                        simbolo=simbolo,
                        nome=simbolo.replace(".SA", ""),
                        preco=round(fechamento_atual, 2),
                        variacao_percentual=round(variacao_pct, 2),
                        variacao_valor=round(variacao_valor, 2),
                        volume=volume,
                        moeda=moeda,
                    )
                )
            except Exception as exc:
                self._log.aviso(f"Falha ao ler {simbolo}: {exc}")

        return resultados

    def listar_em_alta(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_acoes_monitoradas(quantidade))
        em_alta = [r for r in resumos if r.variacao_percentual > 0]
        em_alta.sort(key=lambda item: item.variacao_percentual, reverse=True)
        return em_alta[:quantidade]

    def listar_em_queda(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_acoes_monitoradas(quantidade))
        em_queda = [r for r in resumos if r.variacao_percentual < 0]
        em_queda.sort(key=lambda item: item.variacao_percentual)
        return em_queda[:quantidade]

    def listar_todas_monitoradas(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[CotacaoResumo]:
        """Acoes do universo monitorado, ordenadas por codigo."""
        resumos = self.buscar_resumos(self.listar_acoes_monitoradas(quantidade))
        resumos.sort(key=lambda item: item.simbolo)
        return resumos[:quantidade]

    def buscar_historico(
        self,
        simbolo: str,
        periodo_chave: str = "mes",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
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
                dados = yf.download(
                    simbolo,
                    period=cfg["period"],
                    interval=cfg["interval"],
                    progress=False,
                    auto_adjust=True,
                )
                rotulo = periodo_chave

            serie = self._extrair_serie_simbolo(dados, simbolo)
            if serie is None:
                if "Close" in dados.columns:
                    serie = dados
                else:
                    return None

            if serie.empty or "Close" not in serie.columns:
                return None

            pontos: list[PontoHistorico] = []
            for indice, linha in serie.iterrows():
                if linha["Close"] != linha["Close"]:  # NaN
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
                        volume=int(linha["Volume"])
                        if "Volume" in linha and linha["Volume"] == linha["Volume"]
                        else None,
                    )
                )

            if not pontos:
                return None

            return SerieHistorica(simbolo=simbolo, periodo=rotulo, pontos=pontos)
        except Exception as exc:
            self._log.erro(f"Historico {simbolo}: {exc}")
            return None

    def comparar_acoes(
        self,
        simbolos: list[str],
        periodo_chave: str = "mes",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> dict:
        series: dict[str, list[dict]] = {}
        for simbolo in simbolos:
            serie = self.buscar_historico(simbolo, periodo_chave, data_inicio, data_fim)
            if not serie or not serie.pontos:
                continue

            primeiro = serie.pontos[0].preco_fechamento or 1
            series[simbolo] = [
                {
                    "data": p.data_exibicao,
                    "data_iso": p.data_iso,
                    "preco": p.preco_fechamento,
                    "indice_relativo": round((p.preco_fechamento / primeiro) * 100, 2),
                }
                for p in serie.pontos
            ]

        return {"simbolos": list(series.keys()), "series": series}
