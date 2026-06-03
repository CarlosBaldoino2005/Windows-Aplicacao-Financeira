"""Universo de acoes que costumam pagar dividendos (B3 e EUA) para o painel dedicado."""

LIMITE_DIVIDENDOS_PAINEL = 15
QUANTIDADE_PADRAO_DIVIDENDOS = 15
QUANTIDADE_MAXIMA_DIVIDENDOS = 80

# B3: empresas com historico recorrente de proventos (acoes e units).
ACOES_B3_DIVIDENDOS = [
    "PETR3",
    "PETR4",
    "VALE3",
    "ITUB4",
    "BBDC4",
    "BBAS3",
    "WEGE3",
    "TAEE11",
    "CPLE6",
    "EGIE3",
    "SANB11",
    "BBSE3",
    "CMIG4",
    "TRPL4",
    "ELET3",
    "ELET6",
    "ITSA4",
    "SAPR11",
    "KLBN11",
    "VIVT3",
    "TIMS3",
    "SBSP3",
    "PRIO3",
    "RENT3",
    "ABEV3",
    "SUZB3",
    "GGBR4",
    "USIM5",
    "B3SA3",
    "RADL3",
    "LREN3",
    "ENBR3",
    "CPFE3",
    "EQTL3",
    "RAIL3",
    "CCRO3",
    "VBBR3",
    "RDOR3",
    "TOTS3",
    "FLRY3",
    "CYRE3",
    "MRFG3",
    "BEEF3",
    "HAPV3",
    "BPAC11",
    "PSSA3",
    "CXSE3",
    "ALOS3",
]

# EUA: large caps com dividend yield recorrente.
ACOES_EUA_DIVIDENDOS = [
    "AAPL",
    "MSFT",
    "JPM",
    "V",
    "MA",
    "WMT",
    "KO",
    "PEP",
    "XOM",
    "CVX",
    "T",
    "VZ",
    "IBM",
    "MCD",
    "PG",
    "JNJ",
    "HD",
    "ABBV",
    "MRK",
    "CSCO",
    "INTC",
    "AMD",
    "DIS",
    "BAC",
    "WFC",
]


def montar_lista_dividendos_monitoradas(limite: int = LIMITE_DIVIDENDOS_PAINEL) -> list[str]:
    """Monta tickers Yahoo (.SA na B3) ate o limite informado."""
    resultado: list[str] = []
    vistos: set[str] = set()

    for codigo in ACOES_B3_DIVIDENDOS:
        simbolo = f"{codigo}.SA" if not codigo.endswith(".SA") else codigo
        if simbolo not in vistos:
            vistos.add(simbolo)
            resultado.append(simbolo)
        if len(resultado) >= limite:
            return resultado[:limite]

    for codigo in ACOES_EUA_DIVIDENDOS:
        if codigo not in vistos:
            vistos.add(codigo)
            resultado.append(codigo)
        if len(resultado) >= limite:
            break

    return resultado[:limite]


def simbolo_esta_no_universo_dividendos(simbolo: str) -> bool:
    """Verifica se o ticker faz parte da lista curada de pagadoras."""
    limpo = simbolo.strip().upper()
    codigo = limpo.replace(".SA", "")
    if limpo.endswith(".SA"):
        return codigo in ACOES_B3_DIVIDENDOS
    return codigo in ACOES_EUA_DIVIDENDOS
