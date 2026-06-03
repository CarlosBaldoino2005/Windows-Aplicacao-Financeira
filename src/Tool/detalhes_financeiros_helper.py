"""Conversao de DataFrames do yfinance para estruturas da aplicacao."""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.Model.detalhes_acao import LinhaDemonstrativo, PeriodoResultado

# Linhas prioritarias na DRE (tentativa por nome aproximado).
_ROTULOS_RECEITA = (
    "Total Revenue",
    "Operating Revenue",
    "Revenue",
)
_ROTULOS_LUCRO = (
    "Net Income",
    "Net Income Common Stockholders",
    "Net Income From Continuing Operation Net Minority Interest",
    "Normalized Income",
)
_ROTULOS_EBITDA = ("EBITDA", "Normalized EBITDA")
_ROTULOS_EBIT = ("EBIT", "Operating Income")


def _formatar_cabecalho_periodo(valor) -> str:
    if isinstance(valor, (pd.Timestamp, datetime)):
        if valor.month == 12 and valor.day == 31:
            return str(valor.year)
        trimestre = ((valor.month - 1) // 3) + 1
        return f"T{trimestre}/{valor.year}"
    return str(valor)


def _buscar_linha(df: pd.DataFrame, candidatos: tuple[str, ...]) -> str | None:
    if df is None or df.empty:
        return None
    indice = [str(i) for i in df.index]
    for nome in candidatos:
        if nome in indice:
            return nome
    for nome in candidatos:
        for linha in indice:
            if nome.lower() in linha.lower():
                return linha
    return None


def _valor_celula(df: pd.DataFrame, linha: str | None, coluna) -> float | None:
    if not linha or linha not in df.index:
        return None
    try:
        valor = df.loc[linha, coluna]
        if pd.isna(valor):
            return None
        return float(valor)
    except (KeyError, TypeError, ValueError):
        return None


def extrair_periodos_resultado(df: pd.DataFrame, maximo: int = 8) -> list[PeriodoResultado]:
    """Monta lista de trimestres/anos com receita, lucro e EBITDA."""
    if df is None or df.empty:
        return []

    linha_receita = _buscar_linha(df, _ROTULOS_RECEITA)
    linha_lucro = _buscar_linha(df, _ROTULOS_LUCRO)
    linha_ebitda = _buscar_linha(df, _ROTULOS_EBITDA)
    linha_ebit = _buscar_linha(df, _ROTULOS_EBIT)

    resultado: list[PeriodoResultado] = []
    colunas = list(df.columns)[:maximo]

    for coluna in colunas:
        resultado.append(
            PeriodoResultado(
                periodo=_formatar_cabecalho_periodo(coluna),
                receita=_valor_celula(df, linha_receita, coluna),
                lucro_liquido=_valor_celula(df, linha_lucro, coluna),
                ebitda=_valor_celula(df, linha_ebitda, coluna),
                lucro_operacional=_valor_celula(df, linha_ebit, coluna),
            )
        )

    return resultado


def extrair_linhas_demonstrativo(
    df: pd.DataFrame,
    rotulos: tuple[str, ...],
    max_periodos: int = 6,
) -> list[LinhaDemonstrativo]:
    """Extrai linhas selecionadas do demonstrativo para exibicao em tabela."""
    if df is None or df.empty:
        return []

    colunas = list(df.columns)[:max_periodos]
    cabecalhos = [_formatar_cabecalho_periodo(c) for c in colunas]
    saida: list[LinhaDemonstrativo] = []

    for rotulo in rotulos:
        linha = _buscar_linha(df, (rotulo,))
        if not linha:
            continue
        valores = {}
        for cab, col in zip(cabecalhos, colunas, strict=True):
            numero = _valor_celula(df, linha, col)
            if numero is not None:
                valores[cab] = numero
        if valores:
            saida.append(LinhaDemonstrativo(rotulo=linha, valores=valores))

    return saida


LINHAS_DRE = (
    "Total Revenue",
    "Gross Profit",
    "Operating Income",
    "EBITDA",
    "Net Income",
    "Basic EPS",
)

LINHAS_BALANCO = (
    "Total Assets",
    "Total Liabilities Net Minority Interest",
    "Stockholders Equity",
    "Cash And Cash Equivalents",
    "Total Debt",
)

LINHAS_FLUXO = (
    "Operating Cash Flow",
    "Investing Cash Flow",
    "Financing Cash Flow",
    "Free Cash Flow",
    "Capital Expenditure",
)
