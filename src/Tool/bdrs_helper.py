"""Validacao de BDRs (acoes globais negociadas na B3)."""
from __future__ import annotations

import re

from src.Model.acoes_bdr_universo import simbolo_esta_no_universo_bdrs

# Padrao usual de BDR na B3: quatro letras + 34 ou 35 + .SA.
_PADRAO_BDR_B3 = re.compile(r"^[A-Z]{4}3[245]\.SA$")


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
