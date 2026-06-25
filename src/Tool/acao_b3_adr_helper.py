"""Mapeamento de acoes B3 para ADRs nos EUA (movimentos de analistas)."""
from __future__ import annotations

import re

from src.Tool.bdrs_helper import eh_bdr_b3
from src.Tool.etfs_helper import eh_etf
from src.Tool.fiis_helper import eh_fii

# Base do codigo B3 (4 letras) -> ticker ADR/acao nos EUA no Yahoo Finance.
_MAPA_BASE_ACAO_B3_PARA_ADR: dict[str, str] = {
    "ABEV": "ABEV",
    "ASAI": "ASAI",
    "BBDC": "BBD",
    "BBAS": "BBAS",
    "BRFS": "BRFS",
    "BSBR": "BSBR",
    "CCRO": "CCRO",
    "CMIG": "CIG",
    "CPFE": "CPFE",
    "CPLE": "CPL",
    "CSAN": "CSAN",
    "CSNA": "SID",
    "EGIE": "EGIEY",
    "ELET": "EBR",
    "EMBR": "ERJ",
    "EQTL": "EQTL",
    "GGBR": "GGB",
    "GOLL": "GOL",
    "HAPV": "HMY",
    "ITUB": "ITUB",
    "JBSS": "JBS",
    "KLBN": "KLBN",
    "LREN": "LREN",
    "MRFG": "MRFG",
    "MGLU": "MGLU",
    "NTCO": "NTCO",
    "PCAR": "PAGS",
    "PETR": "PBR",
    "PRIO": "PRIO",
    "RADL": "RADL",
    "RAIL": "RAIL",
    "RENT": "RTO",
    "SANB": "BSBR",
    "SBSP": "SBS",
    "SLCE": "SLCE",
    "SMTO": "SMTO",
    "SUZB": "SUZ",
    "TAEE": "TAEE",
    "TIMS": "TIMB",
    "UGPA": "UGP",
    "USIM": "USIM",
    "VALE": "VALE",
    "VBBR": "VBBR",
    "VIVT": "VIV",
    "WEGE": "WEGZY",
}


def codigo_base_acao_b3(simbolo: str) -> str | None:
    """Extrai as 4 letras do codigo B3 (ex.: PETR4.SA -> PETR)."""
    codigo = (simbolo or "").strip().upper().replace(".SA", "")
    if len(codigo) != 5:
        return None
    if not codigo[:4].isalpha() or not codigo[4].isdigit():
        return None
    return codigo[:4]


def eh_acao_b3_para_adr(simbolo: str) -> bool:
    """Acao ordinaria/preferencial na B3 (nao FII, ETF nem BDR)."""
    limpo = (simbolo or "").strip().upper()
    if not limpo.endswith(".SA"):
        return False
    if eh_bdr_b3(limpo) or eh_fii(limpo) or eh_etf(limpo):
        return False
    return codigo_base_acao_b3(limpo) is not None


def resolver_adr_eua_para_acao_b3(simbolo: str) -> str | None:
    """
    Retorna ticker nos EUA para buscar movimentos de analistas.
    Ex.: PETR4.SA -> PBR, VALE3.SA -> VALE.
    """
    if not eh_acao_b3_para_adr(simbolo):
        return None
    base = codigo_base_acao_b3(simbolo)
    if base is None:
        return None
    return _MAPA_BASE_ACAO_B3_PARA_ADR.get(base)
