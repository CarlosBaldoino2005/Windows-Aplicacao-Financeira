"""Grupos de acoes do mesmo setor/industria para comparacao de concorrentes."""

# Tickers sem sufixo .SA (B3) ou codigo direto (EUA).
CONCORRENTES_POR_INDUSTRIA: dict[str, list[str]] = {
    "Oil & Gas Integrated": ["PETR3", "PETR4", "PRIO3", "VBBR3", "RRRP3", "CSAN3"],
    "Other Industrial Metals & Mining": ["VALE3", "GGBR4", "USIM5", "CSNA3"],
    "Banks - Regional": ["ITUB4", "BBDC4", "BBDC3", "BBAS3", "SANB11", "BPAC11", "ITSA4"],
    "Electrical Equipment & Parts": ["WEGE3", "ELET3", "ELET6", "EMBR3"],
    "Specialty Retail": ["MGLU3", "LREN3", "RADL3", "CRFB3"],
    "Beverages - Brewers": ["ABEV3"],
    "Insurance - Diversified": ["BBSE3", "SULA11"],
    "Utilities - Regulated Electric": ["EGIE3", "CPLE6", "ENBR3", "TAEE11", "CMIG4"],
    "Utilities - Renewable": ["EGIE3", "CPLE6"],
    "Packaging & Containers": ["KLBN11", "SUZB3"],
    "Airlines": ["AZUL4", "GOLL4"],
    "Medical Care Facilities": ["HAPV3", "RDOR3", "FLRY3"],
    "Real Estate - Diversified": ["CYRE3"],
    "Education & Training Services": ["YDUQ3"],
    "Software - Application": ["TOTS3"],
    "Packaged Foods": ["MRFG3", "BEEF3", "NTCO3"],
    "Telecom Services": ["VIVT3", "TIMS3"],
    "Exchange": ["B3SA3"],
    "Rental & Leasing Services": ["RENT3"],
    "Steel": ["GGBR4", "USIM5", "CSNA3"],
    "Consumer Electronics": ["AAPL", "MSFT", "GOOGL", "META", "AMZN"],
    "Software - Infrastructure": ["MSFT", "ORCL", "CRM", "ADBE"],
    "Semiconductors": ["NVDA", "AMD", "INTC", "AVGO", "QCOM"],
    "Internet Retail": ["AMZN", "MELI", "SHOP"],
    "Auto Manufacturers": ["TSLA", "F", "GM", "RIVN"],
    "Entertainment": ["DIS", "NFLX", "WBD"],
    "Credit Services": ["V", "MA", "AXP", "PYPL"],
    "Banks - Diversified": ["JPM", "BAC", "C", "WFC"],
}

CONCORRENTES_POR_SETOR: dict[str, list[str]] = {
    "Energy": ["PETR3", "PETR4", "PRIO3", "VBBR3", "RRRP3", "CSAN3"],
    "Basic Materials": ["VALE3", "GGBR4", "USIM5", "CSNA3", "SUZB3", "KLBN11"],
    "Financial Services": ["ITUB4", "BBDC4", "BBAS3", "SANB11", "BPAC11", "B3SA3", "JPM", "V", "MA"],
    "Industrials": ["WEGE3", "RENT3", "EMBR3", "GGBR4"],
    "Consumer Cyclical": ["MGLU3", "LREN3", "RADL3", "RENT3", "AMZN", "TSLA", "DIS"],
    "Consumer Defensive": ["ABEV3", "WMT", "PG", "KO"],
    "Utilities": ["EGIE3", "CPLE6", "ENBR3", "TAEE11", "CMIG4"],
    "Healthcare": ["HAPV3", "RDOR3", "FLRY3"],
    "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMD", "INTC"],
    "Communication Services": ["VIVT3", "TIMS3", "META", "GOOGL", "NFLX", "DIS"],
}


def listar_codigos_concorrentes(industria: str | None, setor: str | None, codigo_atual: str, limite: int = 8) -> list[str]:
    """Retorna codigos de possiveis concorrentes, excluindo a acao atual."""
    candidatos: list[str] = []

    if industria and industria in CONCORRENTES_POR_INDUSTRIA:
        candidatos.extend(CONCORRENTES_POR_INDUSTRIA[industria])

    if setor and setor in CONCORRENTES_POR_SETOR:
        candidatos.extend(CONCORRENTES_POR_SETOR[setor])

    resultado: list[str] = []
    vistos: set[str] = set()
    atual = codigo_atual.upper().replace(".SA", "")

    for codigo in candidatos:
        limpo = codigo.upper().replace(".SA", "")
        if limpo == atual or limpo in vistos:
            continue
        vistos.add(limpo)
        resultado.append(limpo)
        if len(resultado) >= limite:
            break

    return resultado
