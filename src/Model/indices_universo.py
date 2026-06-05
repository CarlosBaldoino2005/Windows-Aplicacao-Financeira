"""Indices de mercado monitorados no painel mobile e desktop."""

from dataclasses import dataclass

QUANTIDADE_PADRAO_INDICES = 20
QUANTIDADE_MAXIMA_INDICES = 30


@dataclass(frozen=True)
class IndiceMercado:
    """Um indice ou ETF de referencia."""

    simbolo: str
    nome: str
    regiao: str


INDICES_MERCADO: tuple[IndiceMercado, ...] = (
    IndiceMercado("^BVSP", "Ibovespa", "Brasil"),
    IndiceMercado("^IFIX", "IFIX (Fundos Imobiliarios)", "Brasil"),
    IndiceMercado("BOVA11.SA", "ETF Ibovespa (BOVA11)", "Brasil"),
    IndiceMercado("SMAL11.SA", "ETF Small Caps (SMAL11)", "Brasil"),
    IndiceMercado("^GSPC", "S&P 500", "EUA"),
    IndiceMercado("^IXIC", "Nasdaq Composite", "EUA"),
    IndiceMercado("^DJI", "Dow Jones", "EUA"),
    IndiceMercado("SPY", "ETF S&P 500 (SPY)", "EUA"),
    IndiceMercado("QQQ", "ETF Nasdaq (QQQ)", "EUA"),
    IndiceMercado("^STOXX50E", "Euro Stoxx 50", "Europa"),
    IndiceMercado("^FTSE", "FTSE 100", "Europa"),
    IndiceMercado("^N225", "Nikkei 225", "Asia"),
    IndiceMercado("^HSI", "Hang Seng", "Asia"),
    IndiceMercado("EWZ", "ETF Brasil (EWZ)", "Global"),
    IndiceMercado("DIA", "ETF Dow Jones (DIA)", "EUA"),
)


def listar_simbolos_indices(quantidade: int = QUANTIDADE_PADRAO_INDICES) -> list[str]:
    """Retorna simbolos dos indices para consulta de cotacao."""
    limite = max(1, min(quantidade, len(INDICES_MERCADO)))
    return [item.simbolo for item in INDICES_MERCADO[:limite]]
