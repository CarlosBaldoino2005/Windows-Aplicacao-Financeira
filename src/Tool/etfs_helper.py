"""Validacao de ETFs (B3 e internacionais)."""
from __future__ import annotations

from src.Model.etfs_universo import simbolo_esta_no_universo_etfs


def eh_etf(simbolo: str) -> bool:
    """Indica se o ticker e um ETF conhecido (lista curada ou padrao Yahoo)."""
    limpo = (simbolo or "").strip().upper()
    if not limpo:
        return False
    return simbolo_esta_no_universo_etfs(limpo)
