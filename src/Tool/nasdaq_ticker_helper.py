"""Resolve ticker negociado na Nasdaq (EUA) a partir do simbolo da tela Agora."""
from __future__ import annotations

import re

from src.Tool.acao_b3_adr_helper import (
    eh_acao_b3_para_adr,
    resolver_adr_eua_para_acao_b3,
)
from src.Tool.bdrs_helper import eh_bdr_b3, resolver_ticker_eua_para_bdr


def resolver_ticker_nasdaq(simbolo: str) -> tuple[str | None, str | None]:
    """
    Obtem o ticker nos EUA para grafico intraday na Nasdaq.

    BDRs e ADRs mapeados retornam o ticker subjacente; tickers ja dos EUA
    (ex.: AAPL, SPCX) sao usados diretamente.
    """
    limpo = (simbolo or "").strip().upper()
    if not limpo:
        return None, "Informe um ativo valido."

    if eh_bdr_b3(limpo):
        ticker = resolver_ticker_eua_para_bdr(limpo)
        if ticker:
            return ticker, None
        return None, (
            "Nao foi possivel identificar o ticker nos EUA para este BDR. "
            "Tente um ativo com BDR conhecido (ex.: AAPL34, MSFT34)."
        )

    if limpo.endswith(".SA"):
        if eh_acao_b3_para_adr(limpo):
            adr = resolver_adr_eua_para_acao_b3(limpo)
            if adr:
                return adr, None
        return None, (
            "Esta acao da B3 nao possui ADR/ticker Nasdaq mapeado no sistema."
        )

    codigo = limpo.replace(".SA", "")
    if re.match(r"^[A-Z][A-Z0-9.\-]{0,9}$", codigo):
        return codigo, None

    return None, "Nao foi possivel identificar o ticker na Nasdaq para este ativo."
