"""Validacao de BDRs (acoes globais negociadas na B3)."""
from __future__ import annotations

import re

from src.Model.acoes_bdr_universo import simbolo_esta_no_universo_bdrs

# Padrao usual de BDR na B3: quatro letras + 34 ou 35 + .SA.
_PADRAO_BDR_B3 = re.compile(r"^[A-Z]{4}3[245]\.SA$")

# Ticker nos EUA correspondente ao codigo BDR (excecoes ao prefixo de 4 letras).
_MAPA_CODIGO_BDR_PARA_TICKER_EUA: dict[str, str] = {
    "AAPL34": "AAPL",
    "MSFT34": "MSFT",
    "AMZO34": "AMZN",
    "GOGL34": "GOOGL",
    "META34": "META",
    "TSLA34": "TSLA",
    "NVDC34": "NVDA",
    "NFLX34": "NFLX",
    "INTC34": "INTC",
    "AMDG34": "AMD",
    "CSCO34": "CSCO",
    "ORCL34": "ORCL",
    "ADBE34": "ADBE",
    "CRMG34": "CRM",
    "PYPL34": "PYPL",
    "UBER34": "UBER",
    "SNAP34": "SNAP",
    "SHOP34": "SHOP",
    "IBMG34": "IBM",
    "NOWG34": "NOW",
    "JPMC34": "JPM",
    "BOAC34": "BAC",
    "WFCO34": "WFC",
    "VISA34": "V",
    "BLAK34": "BLK",
    "GSGI34": "GS",
    "MCDC34": "MCD",
    "COCA34": "KO",
    "PEPB34": "PEP",
    "WALT34": "DIS",
    "DISB34": "DIS",
    "NIKE34": "NKE",
    "STBZ34": "SBUX",
    "XOMC34": "XOM",
    "CVXC34": "CVX",
    "CATP34": "CAT",
    "BOEI34": "BA",
    "PFIZ34": "PFE",
    "JNJG34": "JNJ",
    "LLYG34": "LLY",
    "ABBV34": "ABBV",
    "MRKG34": "MRK",
    "BIDU34": "BIDU",
    "MELI34": "MELI",
    "BERK34": "BRK-B",
    "AVGO34": "AVGO",
    "QCOM34": "QCOM",
    "TXNC34": "TXN",
    "PGCO34": "PG",
    "UNHH34": "UNH",
    "HDNG34": "HD",
    "LOWC34": "LOW",
    "TGTG34": "TGT",
    "COST34": "COST",
    "COIN34": "COIN",
    "AIRB34": "ABNB",
    "ABNB34": "ABNB",
    "BKNG34": "BKNG",
    "REGN34": "REGN",
    "GILD34": "GILD",
    "BIIB34": "BIIB",
    "AMGN34": "AMGN",
    "TMUS34": "TMUS",
    "GEOO34": "GE",
    "HONB34": "HON",
    "DEUC34": "DE",
    "SAPR34": "SAP",
    "MDLZ34": "MDLZ",
    "EWDC34": "EW",
    "MACG34": "MCD",
}


def eh_bdr_b3(simbolo: str) -> bool:
    """Indica se o ticker e um BDR negociado na B3."""
    limpo = (simbolo or "").strip().upper()
    if not limpo:
        return False
    if not limpo.endswith(".SA"):
        limpo = f"{limpo}.SA"
    if simbolo_esta_no_universo_bdrs(limpo):
        return True
    return bool(_PADRAO_BDR_B3.match(limpo))


def codigo_bdr_sem_sufixo(simbolo: str) -> str:
    """Retorna o codigo BDR sem .SA (ex.: SPCX34.SA -> SPCX34)."""
    return (simbolo or "").strip().upper().replace(".SA", "")


def resolver_ticker_eua_para_bdr(simbolo_bdr: str) -> str | None:
    """
    Tenta obter o ticker nos EUA do ativo subjacente a um BDR.
    Ex.: SPCX34.SA -> SPCX, AMZO34.SA -> AMZN.
    """
    codigo = codigo_bdr_sem_sufixo(simbolo_bdr)
    if not codigo:
        return None

    if codigo in _MAPA_CODIGO_BDR_PARA_TICKER_EUA:
        return _MAPA_CODIGO_BDR_PARA_TICKER_EUA[codigo]

    if re.match(r"^[A-Z]{4}3[245]$", codigo):
        return codigo[:4]

    return None
