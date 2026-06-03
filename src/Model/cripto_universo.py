"""Universo de criptomoedas monitoradas no painel (pares USD no Yahoo Finance)."""

LIMITE_CRIPTO_PAINEL = 15
QUANTIDADE_PADRAO_CRIPTO = 15
QUANTIDADE_MAXIMA_CRIPTO = 80

# Principais criptos (ticker Yahoo: MOEDA-USD).
CRIPTOMOEDAS_MONITORADAS = [
    "BTC-USD",
    "ETH-USD",
    "BNB-USD",
    "XRP-USD",
    "SOL-USD",
    "ADA-USD",
    "DOGE-USD",
    "AVAX-USD",
    "DOT-USD",
    "LINK-USD",
    "MATIC-USD",
    "POL-USD",
    "LTC-USD",
    "BCH-USD",
    "ATOM-USD",
    "UNI-USD",
    "ETC-USD",
    "XLM-USD",
    "FIL-USD",
    "APT-USD",
    "ARB-USD",
    "OP-USD",
    "NEAR-USD",
    "ICP-USD",
    "HBAR-USD",
    "VET-USD",
    "ALGO-USD",
    "AAVE-USD",
    "GRT-USD",
    "SAND-USD",
    "MANA-USD",
    "AXS-USD",
    "EGLD-USD",
    "XTZ-USD",
    "THETA-USD",
    "EOS-USD",
]

NOMES_CRIPTO: dict[str, str] = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "BNB-USD": "BNB",
    "XRP-USD": "Ripple",
    "SOL-USD": "Solana",
    "ADA-USD": "Cardano",
    "DOGE-USD": "Dogecoin",
    "AVAX-USD": "Avalanche",
    "DOT-USD": "Polkadot",
    "LINK-USD": "Chainlink",
    "MATIC-USD": "Polygon (MATIC)",
    "POL-USD": "Polygon (POL)",
    "LTC-USD": "Litecoin",
    "BCH-USD": "Bitcoin Cash",
    "ATOM-USD": "Cosmos",
    "UNI-USD": "Uniswap",
}


def montar_lista_cripto_monitoradas(limite: int = LIMITE_CRIPTO_PAINEL) -> list[str]:
    """Retorna ate N tickers da lista padrao de criptomoedas."""
    limite_ok = max(1, min(limite, len(CRIPTOMOEDAS_MONITORADAS), QUANTIDADE_MAXIMA_CRIPTO))
    return list(CRIPTOMOEDAS_MONITORADAS[:limite_ok])
