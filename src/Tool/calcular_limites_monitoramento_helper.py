"""Calculo de limites de monitoramento a partir do preco atual."""
from __future__ import annotations

from src.Tool.validadores import validar_limites_monitoramento


def validar_percentual_margem(texto: str, *, maximo: float = 99.0) -> tuple[float | None, str | None]:
    """Valida porcentagem positiva para margem acima/abaixo do preco (ex.: 10 = 10%)."""
    if not texto or not str(texto).strip():
        return None, "Informe a porcentagem."

    limpo = str(texto).strip().replace("%", "").replace(",", ".")
    if not limpo:
        return None, "Informe a porcentagem."

    try:
        valor = float(limpo)
    except ValueError:
        return None, "Porcentagem invalida. Use apenas numeros."

    if valor <= 0:
        return None, "A porcentagem deve ser maior que zero."
    if valor > maximo:
        return None, f"A porcentagem maxima e {maximo:.0f}%."

    return round(valor, 4), None


def calcular_limites_por_margem_valor(preco_atual: float, margem: float) -> tuple[float, float]:
    """Retorna (valor_baixo, valor_alto) simetricos em torno do preco."""
    if preco_atual <= 0:
        raise ValueError("Preco atual invalido.")
    if margem <= 0:
        raise ValueError("Margem invalida.")

    valor_baixo = round(preco_atual - margem, 4)
    valor_alto = round(preco_atual + margem, 4)
    return valor_baixo, valor_alto


def calcular_limites_por_margem_percentual(
    preco_atual: float,
    percentual: float,
) -> tuple[float, float]:
    """Retorna limites percentuais abaixo e acima do preco (ex.: 10 -> -10% / +10%)."""
    if preco_atual <= 0:
        raise ValueError("Preco atual invalido.")
    if percentual <= 0:
        raise ValueError("Percentual invalido.")

    fator = percentual / 100.0
    valor_baixo = round(preco_atual * (1.0 - fator), 4)
    valor_alto = round(preco_atual * (1.0 + fator), 4)
    return valor_baixo, valor_alto


def calcular_limites_monitoramento(
    preco_atual: float,
    *,
    margem_valor: float | None = None,
    margem_percentual: float | None = None,
    moeda: str = "BRL",
) -> tuple[float | None, float | None, str | None]:
    """
    Calcula valor baixo e alto e valida em relacao ao preco atual.
    Informe margem_valor OU margem_percentual.
    """
    if preco_atual <= 0:
        return None, None, "Preco atual indisponivel para calcular os limites."

    try:
        if margem_valor is not None:
            valor_baixo, valor_alto = calcular_limites_por_margem_valor(preco_atual, margem_valor)
        elif margem_percentual is not None:
            valor_baixo, valor_alto = calcular_limites_por_margem_percentual(
                preco_atual,
                margem_percentual,
            )
        else:
            return None, None, "Informe a margem em reais ou em porcentagem."
    except ValueError as exc:
        return None, None, str(exc)

    if valor_baixo <= 0:
        return None, None, "O valor baixo calculado ficou zero ou negativo. Reduza a margem."

    erro = validar_limites_monitoramento(valor_baixo, valor_alto, preco_atual, moeda)
    if erro:
        return None, None, erro

    return valor_baixo, valor_alto, None
