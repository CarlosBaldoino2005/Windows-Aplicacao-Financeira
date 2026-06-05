"""Validacao de fundos imobiliarios (FIIs) da B3."""
from __future__ import annotations

from src.Model.fiis_universo import UNIDADES_NAO_FII, simbolo_esta_no_universo_fiis


def eh_fii(simbolo: str) -> bool:
    """Indica se o ticker e um fundo imobiliario brasileiro (lista curada ou padrao 11)."""
    limpo = (simbolo or "").strip().upper()
    if not limpo.endswith(".SA"):
        return False

    if simbolo_esta_no_universo_fiis(limpo):
        return True

    codigo = limpo.replace(".SA", "")
    if not codigo.endswith("11"):
        return False
    if codigo in UNIDADES_NAO_FII:
        return False

    # Fora da lista curada: aceita somente padrao FII de 4 letras + 11 (ex.: HGLG11).
    prefixo = codigo[:-2]
    return len(prefixo) == 4 and prefixo.isalpha()
