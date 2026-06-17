"""Mapeamento de periodos da interface para cada provedor de mercado."""

# Periodo sem chave nativa no Yahoo: baixa por quantidade de dias.
_MARCA_PERIOD_DIAS = "__dias__"

MAPEAMENTO_PERIODO_YFINANCE = {
    "agora": {"period": "1d", "interval": "1m"},
    "dia": {"period": "1d", "interval": "5m"},
    "semana": {"period": "5d", "interval": "30m"},
    "mes": {"period": "1mo", "interval": "1d"},
    "trimestre": {"period": "3mo", "interval": "1d"},
    "semestre": {"period": "6mo", "interval": "1d"},
    "ano": {"period": "1y", "interval": "1d"},
    "tres_anos": {"period": _MARCA_PERIOD_DIAS, "interval": "1d", "dias": 365 * 3},
    "cinco_anos": {"period": "5y", "interval": "1d"},
}

MAPEAMENTO_PERIODO_YAHOO_CHART = {
    "agora": {"range": "1d", "interval": "1m"},
    "dia": {"range": "1d", "interval": "5m"},
    "semana": {"range": "5d", "interval": "30m"},
    "mes": {"range": "1mo", "interval": "1d"},
    "trimestre": {"range": "3mo", "interval": "1d"},
    "semestre": {"range": "6mo", "interval": "1d"},
    "ano": {"range": "1y", "interval": "1d"},
    "tres_anos": {"range": _MARCA_PERIOD_DIAS, "interval": "1d", "dias": 365 * 3},
    "cinco_anos": {"range": "5y", "interval": "1d"},
}

MAPEAMENTO_PERIODO_BRAPI = {
    "agora": {"range": "1d", "interval": "1d"},
    "dia": {"range": "1d", "interval": "1d"},
    "semana": {"range": "5d", "interval": "1d"},
    "mes": {"range": "1mo", "interval": "1d"},
    "trimestre": {"range": "3mo", "interval": "1d"},
    "semestre": {"range": "6mo", "interval": "1d"},
    "ano": {"range": "1y", "interval": "1d"},
    "tres_anos": {"range": "5y", "interval": "1d", "dias": 365 * 3},
    "cinco_anos": {"range": "5y", "interval": "1d"},
}

# Retrocompatibilidade com mercado_servico.
MAPEAMENTO_PERIODO = MAPEAMENTO_PERIODO_YFINANCE


def periodo_usa_janela_em_dias(cfg: dict) -> bool:
    """True quando o periodo deve ser calculado com start/end (ex.: 3 anos)."""
    return cfg.get("period") == _MARCA_PERIOD_DIAS or cfg.get("range") == _MARCA_PERIOD_DIAS


def dias_do_periodo(cfg: dict) -> int | None:
    """Quantidade de dias para recorte quando o provedor nao tem range exato."""
    dias = cfg.get("dias")
    if dias is None:
        return None
    try:
        return int(dias)
    except (TypeError, ValueError):
        return None
