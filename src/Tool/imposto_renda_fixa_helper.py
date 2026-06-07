"""Calculo de IR regressivo e IOF para renda fixa (Tesouro, CDI, etc.)."""
from __future__ import annotations


def obter_aliquota_ir_regressiva(dias_corridos: int) -> float:
    """Retorna aliquota decimal (ex.: 0.15 para 15%) conforme dias da aplicacao."""
    if dias_corridos <= 0:
        return 0.225
    if dias_corridos <= 180:
        return 0.225
    if dias_corridos <= 360:
        return 0.20
    if dias_corridos <= 720:
        return 0.175
    return 0.15


def obter_aliquota_ir_regressiva_percentual(dias_corridos: int) -> float:
    """Aliquota em percentual para exibicao (ex.: 15.0)."""
    return obter_aliquota_ir_regressiva(dias_corridos) * 100.0


def calcular_iof_sobre_rendimento(rendimento: float, dias_corridos: int) -> float:
    """
    IOF regressivo sobre o rendimento para resgates antes de 30 dias.
    Tabela: dia 1 = 96%, reduz 3 p.p. por dia ate zerar no dia 30.
    """
    if rendimento <= 0 or dias_corridos >= 30:
        return 0.0
    if dias_corridos <= 0:
        dias_corridos = 1
    aliquota_pct = max(0.0, 96.0 - (dias_corridos - 1) * 3.0)
    return round(rendimento * aliquota_pct / 100.0, 2)


def calcular_imposto_renda(rendimento_tributavel: float, dias_corridos: int) -> tuple[float, float]:
    """
    Calcula IR sobre rendimento positivo.
    Retorna (valor_ir, aliquota_percentual).
    """
    if rendimento_tributavel <= 0:
        return 0.0, obter_aliquota_ir_regressiva_percentual(dias_corridos)
    aliquota = obter_aliquota_ir_regressiva(dias_corridos)
    return round(rendimento_tributavel * aliquota, 2), aliquota * 100.0
