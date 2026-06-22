"""Conversao e rotulos para exibir cotacao em real e dolar."""
from __future__ import annotations

from src.Tool.etfs_helper import eh_etf
from src.Tool.fiis_helper import eh_fii


def codigo_exibicao(simbolo: str) -> str:
    """Remove sufixos Yahoo para exibir o codigo na tela."""
    return simbolo.replace(".SA", "").replace("-USD", "")


def rotulo_tipo_ativo(simbolo: str) -> str:
    """Identifica se o ativo e acao, cripto ou fundo imobiliario."""
    if simbolo.endswith("-USD"):
        return "Criptomoeda"
    if eh_fii(simbolo):
        return "Fundo imobiliario"
    if eh_etf(simbolo):
        return "ETF"
    return "Acao"


def calcular_precos_brl_usd(
    preco: float,
    moeda: str,
    taxa_usd_brl: float | None,
) -> tuple[float | None, float | None]:
    """
    Converte o preco para BRL e USD.
    taxa_usd_brl = quantos reais valem 1 dolar.
    """
    if preco <= 0:
        return None, None
    if not taxa_usd_brl or taxa_usd_brl <= 0:
        if moeda == "BRL":
            return preco, None
        return None, preco

    if moeda == "BRL":
        return preco, preco / taxa_usd_brl
    return preco * taxa_usd_brl, preco
