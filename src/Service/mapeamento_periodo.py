"""Mapeamento de periodos da interface para cada provedor de mercado."""

MAPEAMENTO_PERIODO_YFINANCE = {
    "dia": {"period": "1d", "interval": "5m"},
    "semana": {"period": "5d", "interval": "30m"},
    "mes": {"period": "1mo", "interval": "1d"},
    "trimestre": {"period": "3mo", "interval": "1d"},
    "semestre": {"period": "6mo", "interval": "1d"},
    "ano": {"period": "1y", "interval": "1d"},
}

MAPEAMENTO_PERIODO_YAHOO_CHART = {
    "dia": {"range": "1d", "interval": "5m"},
    "semana": {"range": "5d", "interval": "30m"},
    "mes": {"range": "1mo", "interval": "1d"},
    "trimestre": {"range": "3mo", "interval": "1d"},
    "semestre": {"range": "6mo", "interval": "1d"},
    "ano": {"range": "1y", "interval": "1d"},
}

MAPEAMENTO_PERIODO_BRAPI = {
    "dia": {"range": "1d", "interval": "1d"},
    "semana": {"range": "5d", "interval": "1d"},
    "mes": {"range": "1mo", "interval": "1d"},
    "trimestre": {"range": "3mo", "interval": "1d"},
    "semestre": {"range": "6mo", "interval": "1d"},
    "ano": {"range": "1y", "interval": "1d"},
}

# Retrocompatibilidade com mercado_servico.
MAPEAMENTO_PERIODO = MAPEAMENTO_PERIODO_YFINANCE
