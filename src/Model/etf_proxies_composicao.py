"""Proxies Yahoo para composicao quando o ETF da B3 nao expoe holdings."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProxyComposicaoEtf:
    """ETF internacional usado como referencia de composicao."""

    simbolo_yahoo: str
    aviso: str


# Codigo B3 (sem .SA) -> proxy com mensagem clara ao usuario.
PROXIES_COMPOSICAO_ETF_B3: dict[str, ProxyComposicaoEtf] = {
    "BOVA11": ProxyComposicaoEtf(
        "EWZ",
        "O Yahoo nao publica a carteira do BOVA11. Exibimos as principais posicoes "
        "do ETF iShares MSCI Brazil (EWZ) como referencia de exposicao ao Brasil.",
    ),
    "BOVV11": ProxyComposicaoEtf(
        "EWZ",
        "Carteira de referencia: iShares MSCI Brazil (EWZ). Dados diretos do BOVV11 "
        "indisponiveis no Yahoo Finance.",
    ),
    "BBOV11": ProxyComposicaoEtf(
        "EWZ",
        "Carteira de referencia: iShares MSCI Brazil (EWZ). Dados diretos do BBOV11 "
        "indisponiveis no Yahoo Finance.",
    ),
    "IVVB11": ProxyComposicaoEtf(
        "IVV",
        "O IVVB11 replica o S&P 500. Exibimos as principais posicoes do ETF IVV "
        "(mesmo indice de referencia).",
    ),
    "SPXI11": ProxyComposicaoEtf(
        "SPY",
        "Carteira de referencia: SPY (S&P 500). Dados diretos do SPXI11 indisponiveis "
        "no Yahoo Finance.",
    ),
    "NASD11": ProxyComposicaoEtf(
        "QQQ",
        "O NASD11 acompanha o Nasdaq. Exibimos as principais posicoes do ETF QQQ.",
    ),
    "SMAL11": ProxyComposicaoEtf(
        "EWZS",
        "Carteira de referencia: iShares MSCI Brazil Small-Cap (EWZS). Dados diretos "
        "do SMAL11 indisponiveis no Yahoo Finance.",
    ),
    "SMLL11": ProxyComposicaoEtf(
        "EWZS",
        "Carteira de referencia: iShares MSCI Brazil Small-Cap (EWZS). Dados diretos "
        "do SMLL11 indisponiveis no Yahoo Finance.",
    ),
    "WRLD11": ProxyComposicaoEtf(
        "VT",
        "Carteira de referencia: Vanguard Total World Stock (VT). Dados diretos do "
        "WRLD11 indisponiveis no Yahoo Finance.",
    ),
    "ACWI11": ProxyComposicaoEtf(
        "ACWI",
        "Carteira de referencia: iShares MSCI ACWI (ACWI). Dados diretos do ACWI11 "
        "indisponiveis no Yahoo Finance.",
    ),
    "GOLD11": ProxyComposicaoEtf(
        "GLD",
        "Carteira de referencia: SPDR Gold Shares (GLD). Dados diretos do GOLD11 "
        "indisponiveis no Yahoo Finance.",
    ),
    "XFIX11": ProxyComposicaoEtf(
        "AGG",
        "Carteira de referencia: iShares Core US Aggregate Bond (AGG). Dados diretos "
        "do XFIX11 indisponiveis no Yahoo Finance.",
    ),
    "EURP11": ProxyComposicaoEtf(
        "VGK",
        "Carteira de referencia: Vanguard FTSE Europe (VGK). Dados diretos do EURP11 "
        "indisponiveis no Yahoo Finance.",
    ),
    "HASH11": ProxyComposicaoEtf(
        "BITO",
        "Carteira de referencia: ProShares Bitcoin Strategy ETF (BITO). Dados diretos "
        "do HASH11 indisponiveis no Yahoo Finance.",
    ),
    "BITH11": ProxyComposicaoEtf(
        "BITO",
        "Carteira de referencia: ProShares Bitcoin Strategy ETF (BITO). Dados diretos "
        "do BITH11 indisponiveis no Yahoo Finance.",
    ),
}


def obter_proxy_composicao(codigo_b3: str) -> ProxyComposicaoEtf | None:
    """Retorna proxy cadastrado para o ticker B3, se houver."""
    limpo = (codigo_b3 or "").strip().upper().replace(".SA", "")
    if not limpo:
        return None
    return PROXIES_COMPOSICAO_ETF_B3.get(limpo)
