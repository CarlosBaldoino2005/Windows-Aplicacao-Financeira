"""Calculo de quantidade de acoes/cotas a partir de um valor em dinheiro."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoQuantidadePorValor:
    """Resultado do calculo valor disponivel / preco unitario."""

    quantidade: int
    valor_investido: float
    valor_sobra: float
    preco_unitario: float


def calcular_quantidade_por_valor(
    valor_disponivel: float,
    preco_unitario: float,
) -> ResultadoQuantidadePorValor:
    """
    Calcula quantas acoes inteiras cabem no valor informado.
    A sobra e o que nao compra uma acao a mais.
    """
    if preco_unitario <= 0:
        return ResultadoQuantidadePorValor(
            quantidade=0,
            valor_investido=0.0,
            valor_sobra=max(0.0, valor_disponivel),
            preco_unitario=preco_unitario,
        )

    quantidade = int(valor_disponivel // preco_unitario)
    valor_investido = round(quantidade * preco_unitario, 2)
    valor_sobra = round(max(0.0, valor_disponivel - valor_investido), 2)

    return ResultadoQuantidadePorValor(
        quantidade=quantidade,
        valor_investido=valor_investido,
        valor_sobra=valor_sobra,
        preco_unitario=preco_unitario,
    )
