"""Universo de ETFs (B3 e internacionais) para o painel dedicado."""

LIMITE_ETFS_PAINEL = 15
QUANTIDADE_PADRAO_ETFS = 15
QUANTIDADE_MAXIMA_ETFS = 80

# ETFs brasileiros (B3) — tickers sem sufixo .SA.
ETFS_B3 = [
    "BOVA11",
    "SMAL11",
    "SMLL11",
    "IVVB11",
    "BOVV11",
    "GOLD11",
    "DIVO11",
    "MATB11",
    "FIND11",
    "XFIX11",
    "NASD11",
    "EURP11",
    "WRLD11",
    "HASH11",
    "BITH11",
    "TECK11",
    "EMBR11",
    "PIIB11",
    "ISUS11",
    "ESGB11",
    "BOVB11",
    "SPXI11",
    "XINA11",
    "ACWI11",
    "BBOV11",
]

# ETFs internacionais (Yahoo sem .SA).
ETFS_INTERNACIONAIS = [
    "SPY",
    "QQQ",
    "EWZ",
    "DIA",
    "VTI",
    "VOO",
    "IWM",
    "IVV",
    "ARKK",
    "XLK",
    "XLF",
    "EEM",
    "GLD",
    "SLV",
]


def montar_lista_etfs_monitorados(limite: int = LIMITE_ETFS_PAINEL) -> list[str]:
    """Monta tickers Yahoo ate o limite informado."""
    resultado: list[str] = []
    vistos: set[str] = set()

    for codigo in ETFS_B3:
        simbolo = f"{codigo}.SA" if not codigo.endswith(".SA") else codigo
        if simbolo not in vistos:
            vistos.add(simbolo)
            resultado.append(simbolo)
        if len(resultado) >= limite:
            return resultado[:limite]

    for codigo in ETFS_INTERNACIONAIS:
        simbolo = codigo.upper()
        if simbolo not in vistos:
            vistos.add(simbolo)
            resultado.append(simbolo)
        if len(resultado) >= limite:
            return resultado[:limite]

    return resultado[:limite]


def simbolo_esta_no_universo_etfs(simbolo: str) -> bool:
    """Verifica se o ticker faz parte da lista curada de ETFs."""
    limpo = simbolo.strip().upper()
    codigo = limpo.replace(".SA", "")
    if codigo in ETFS_B3 or codigo in ETFS_INTERNACIONAIS:
        return True
    return limpo in ETFS_INTERNACIONAIS
