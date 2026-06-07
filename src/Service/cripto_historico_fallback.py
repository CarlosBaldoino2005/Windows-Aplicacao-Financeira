"""Fallback de historico de cripto quando o Yahoo nao tem candles recentes (ex.: MATIC-USD)."""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from src.Model.cotacao import PontoHistorico, SerieHistorica
from src.Tool.registrador_log import RegistradorLog

# Dias retroativos a partir da ultima data publicada no Yahoo (nao a partir de hoje).
_DIAS_POR_PERIODO: dict[str, int] = {
    "dia": 1,
    "semana": 7,
    "mes": 31,
    "trimestre": 92,
    "semestre": 183,
    "ano": 366,
}


def buscar_historico_ultimo_intervalo_disponivel(
    simbolo: str,
    periodo_chave: str,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
) -> SerieHistorica | None:
    """
    Quando period=1mo etc. retorna vazio, baixa period=max e recorta o trecho
    pedido ancorado na ultima data que o Yahoo ainda publicou.
    """
    log = RegistradorLog()
    try:
        if periodo_chave == "personalizado" and data_inicio and data_fim:
            dados = yf.download(
                simbolo,
                start=data_inicio.date(),
                end=(data_fim + timedelta(days=1)).date(),
                interval="1d",
                progress=False,
                auto_adjust=True,
            )
            rotulo = "personalizado"
            aviso_prefixo = ""
        else:
            dados = yf.download(
                simbolo,
                period="max",
                interval="1d",
                progress=False,
                auto_adjust=True,
            )
            rotulo = periodo_chave
            aviso_prefixo = _mensagem_dados_desatualizados(simbolo)

        serie_bruta = _extrair_close(simbolo, dados)
        if serie_bruta is None or serie_bruta.empty:
            return None

        ultima = serie_bruta.index.max()
        ultima_dt = _normalizar_datetime_indice(ultima)
        if ultima_dt is None:
            return None

        if periodo_chave != "personalizado" or not (data_inicio and data_fim):
            dias = _DIAS_POR_PERIODO.get(periodo_chave, 31)
            inicio_janela = ultima_dt - timedelta(days=dias)
            serie_recorte = serie_bruta[serie_bruta.index >= inicio_janela]
        else:
            serie_recorte = serie_bruta

        if serie_recorte.empty:
            return None

        pontos = _pontos_de_serie(serie_recorte)
        if not pontos:
            return None

        data_fim_txt = ultima_dt.strftime("%d/%m/%Y")
        aviso = aviso_prefixo
        if aviso_prefixo:
            aviso = (
                f"{aviso_prefixo} Exibindo o periodo solicitado com dados ate {data_fim_txt}."
            )

        log.info(
            f"Historico {simbolo} ({periodo_chave}) via fallback ultima data Yahoo ({data_fim_txt})"
        )
        return SerieHistorica(simbolo=simbolo, periodo=rotulo, pontos=pontos, aviso=aviso)
    except Exception as exc:
        log.aviso(f"Fallback historico cripto {simbolo}: {exc}")
        return None


def mensagem_erro_historico_cripto(simbolo: str) -> str:
    """Texto amigavel quando nenhum provedor retorna candles."""
    codigo = simbolo.replace("-USD", "")
    if codigo == "MATIC":
        return (
            "Historico indisponivel no Yahoo Finance para MATIC-USD no periodo recente. "
            "A Polygon migrou o token para POL em 2024; o Yahoo encerrou a serie MATIC em "
            "marco/2025. Tente POL-USD ou outro periodo personalizado ate essa data."
        )
    if codigo == "POL":
        return (
            "Historico recente de POL-USD indisponivel no Yahoo Finance. "
            "A serie publicada pelo Yahoo pode estar desatualizada; tente periodo personalizado "
            "ou outra cripto."
        )
    return (
        f"Historico indisponivel para {codigo} neste periodo. "
        "O Yahoo Finance pode nao publicar candles recentes para este par."
    )


def _mensagem_dados_desatualizados(simbolo: str) -> str:
    codigo = simbolo.replace("-USD", "")
    if codigo == "MATIC":
        return (
            "O Yahoo Finance nao atualiza mais MATIC-USD (serie encerrada apos migracao para POL)."
        )
    return f"O Yahoo Finance nao publica cotacoes recentes de {codigo}."


def _extrair_close(simbolo: str, dados) -> pd.Series | None:
    if dados is None or dados.empty:
        return None

    if isinstance(dados.columns, pd.MultiIndex):
        for nivel in ("Ticker", 1, -1):
            try:
                tickers = dados.columns.get_level_values(nivel)
                if simbolo in tickers:
                    frame = dados.xs(simbolo, axis=1, level=nivel)
                    if "Close" in frame.columns:
                        return frame["Close"].dropna()
                    if len(frame.columns) == 1:
                        return frame.iloc[:, 0].dropna()
            except (KeyError, ValueError):
                continue
        try:
            if "Close" in dados.columns.get_level_values(0):
                close = dados["Close"]
                if isinstance(close, pd.DataFrame) and simbolo in close.columns:
                    serie = close[simbolo].dropna()
                    return serie if isinstance(serie, pd.Series) else None
        except (KeyError, ValueError):
            pass
        return None

    if "Close" in dados.columns:
        return dados["Close"].dropna()
    return None


def _normalizar_datetime_indice(valor) -> datetime | None:
    """Converte indice pandas/yfinance em datetime para calculos de periodo."""
    if valor is None:
        return None
    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(valor, datetime):
        return valor
    if hasattr(valor, "to_pydatetime"):
        convertido = valor.to_pydatetime()
        return convertido if isinstance(convertido, datetime) else None
    return None


def _pontos_de_serie(serie: pd.Series) -> list[PontoHistorico]:
    pontos: list[PontoHistorico] = []
    for indice, valor in serie.items():
        if pd.isna(valor):
            continue
        data_obj = indice.to_pydatetime() if hasattr(indice, "to_pydatetime") else indice
        pontos.append(
            PontoHistorico(
                data_iso=data_obj.isoformat(),
                data_exibicao=data_obj.strftime("%d/%m/%Y"),
                preco_fechamento=round(float(valor), 2),
                preco_abertura=None,
                volume=None,
            )
        )
    return pontos
