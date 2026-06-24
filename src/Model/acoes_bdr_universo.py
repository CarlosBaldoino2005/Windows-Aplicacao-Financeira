"""Universo de BDRs (acoes globais negociadas na B3)."""

LIMITE_BDRS_PAINEL = 15
QUANTIDADE_PADRAO_BDRS = 15
QUANTIDADE_MAXIMA_BDRS = 80

# BDRs de empresas internacionais listados na B3 (ticker sem sufixo .SA).
BDRS_B3 = [
    "AAPL34",
    "MSFT34",
    "AMZO34",
    "GOGL34",
    "META34",
    "TSLA34",
    "NVDC34",
    "NFLX34",
    "INTC34",
    "AMDG34",
    "CSCO34",
    "ORCL34",
    "ADBE34",
    "CRMG34",
    "PYPL34",
    "UBER34",
    "SNAP34",
    "SHOP34",
    "IBMG34",
    "NOWG34",
    "JPMC34",
    "BOAC34",
    "WFCO34",
    "VISA34",
    "BLAK34",
    "GSGI34",
    "MCDC34",
    "COCA34",
    "PEPB34",
    "WALT34",
    "DISB34",
    "NIKE34",
    "STBZ34",
    "XOMC34",
    "CVXC34",
    "CATP34",
    "BOEI34",
    "PFIZ34",
    "JNJG34",
    "LLYG34",
    "ABBV34",
    "MRKG34",
    "BIDU34",
    "MELI34",
    "BERK34",
    "AVGO34",
    "QCOM34",
    "TXNC34",
    "PGCO34",
    "UNHH34",
    "HDNG34",
    "LOWC34",
    "TGTG34",
    "COST34",
    "COIN34",
    "AIRB34",
    "DEUC34",
    "SAPR34",
    "MDLZ34",
    "EWDC34",
    "MACG34",
    "ABNB34",
    "BKNG34",
    "REGN34",
    "GILD34",
    "BIIB34",
    "AMGN34",
    "TMUS34",
    "GEOO34",
    "HONB34",
]


def montar_lista_bdrs_monitorados(limite: int = LIMITE_BDRS_PAINEL) -> list[str]:
    """Monta tickers Yahoo (.SA) ate o limite informado."""
    resultado: list[str] = []
    vistos: set[str] = set()

    for codigo in BDRS_B3:
        simbolo = f"{codigo}.SA" if not codigo.endswith(".SA") else codigo
        if simbolo not in vistos:
            vistos.add(simbolo)
            resultado.append(simbolo)
        if len(resultado) >= limite:
            return resultado[:limite]

    return resultado[:limite]


def simbolo_esta_no_universo_bdrs(simbolo: str) -> bool:
    """Verifica se o ticker faz parte da lista curada de BDRs."""
    limpo = simbolo.strip().upper()
    codigo = limpo.replace(".SA", "")
    return codigo in BDRS_B3
