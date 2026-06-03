"""Universo de acoes monitoradas no painel principal (B3 + EUA)."""

LIMITE_ACOES_PAINEL = 10
QUANTIDADE_PADRAO_PAINEL = 10
QUANTIDADE_MAXIMA_PAINEL = 100

# Acoes B3 mais negociadas para o painel.
ACOES_B3_MONITORADAS = [
    "PETR3",
    "PETR4",
    "VALE3",
    "ITUB4",
    "BBDC3",
    "BBDC4",
    "WEGE3",
    "ABEV3",
    "MGLU3",
    "BBAS3",
    "SANB11",
    "B3SA3",
    "SUZB3",
    "RENT3",
    "LREN3",
    "RADL3",
    "VIVT3",
    "TIMS3",
    "CMIG4",
    "CSAN3",
    "GGBR4",
    "USIM5",
    "CSNA3",
    "EMBR3",
    "AZUL4",
    "GOLL4",
    "HAPV3",
    "KLBN11",
    "TAEE11",
    "EGIE3",
    "CPLE6",
    "ENBR3",
    "PRIO3",
    "RRRP3",
    "BPAC11",
    "ITSA4",
    "SBSP3",
    "TRPL4",
    "ELET3",
    "ELET6",
    "VBBR3",
    "RDOR3",
    "NTCO3",
    "MRFG3",
    "BEEF3",
    "TOTS3",
    "FLRY3",
    "CYRE3",
    "YDUQ3",
    "CRFB3",
]

ACOES_EUA_MONITORADAS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "AMD",
    "INTC",
    "NFLX",
    "DIS",
    "JPM",
    "V",
    "MA",
    "WMT",
]


def montar_lista_monitoradas(limite: int = LIMITE_ACOES_PAINEL) -> list[str]:
    """Monta tickers Yahoo (B3 com .SA) ate o limite informado."""
    resultado: list[str] = []
    vistos: set[str] = set()

    for codigo in ACOES_B3_MONITORADAS:
        simbolo = f"{codigo}.SA" if not codigo.endswith(".SA") else codigo
        if simbolo not in vistos:
            vistos.add(simbolo)
            resultado.append(simbolo)
        if len(resultado) >= limite:
            return resultado[:limite]

    for codigo in ACOES_EUA_MONITORADAS:
        if codigo not in vistos:
            vistos.add(codigo)
            resultado.append(codigo)
        if len(resultado) >= limite:
            break

    return resultado[:limite]


# Lista fixa usada pelo painel (quantidade padrao).
ACOES_MONITORADAS = montar_lista_monitoradas()

# Retrocompatibilidade com modulos que importavam ACOES_PADRAO.
ACOES_PADRAO = ACOES_MONITORADAS
