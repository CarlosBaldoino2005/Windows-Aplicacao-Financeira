"""Resumo da posicao na carteira para a tela Agora."""
from __future__ import annotations

from dataclasses import dataclass

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import LinhaCarteira


@dataclass(frozen=True)
class ResumoCarteiraAgora:
    """Quantidade, preco medio e investido para exibir na tela Agora."""

    quantidade: float
    preco_compra: float
    valor_investido: float
    moeda: str = "BRL"

    def valorizacao_reais(self, preco_atual: float) -> float:
        return round(self.quantidade * preco_atual - self.valor_investido, 2)

    def valorizacao_percentual(self, preco_atual: float) -> float | None:
        if self.valor_investido <= 0:
            return None
        return round((self.valorizacao_reais(preco_atual) / self.valor_investido) * 100, 2)

    @classmethod
    def de_linha(cls, linha: LinhaCarteira) -> ResumoCarteiraAgora:
        moeda = linha.cotacao.moeda if linha.cotacao else "BRL"
        return cls(
            quantidade=linha.posicao.quantidade,
            preco_compra=linha.posicao.preco_compra,
            valor_investido=linha.posicao.valor_investido,
            moeda=moeda,
        )


def buscar_resumo_carteira(
    simbolo: str,
    linha: LinhaCarteira | None = None,
) -> ResumoCarteiraAgora | None:
    """Retorna resumo da posicao; usa a linha informada ou agrega por simbolo."""
    if linha is not None:
        return ResumoCarteiraAgora.de_linha(linha)

    controlador = ControladorCarteira()
    linhas, erro = controlador.obter_linhas_carteira()
    if erro or not linhas:
        return None

    simbolo_norm = simbolo.strip().upper()
    correspondentes = [
        item for item in linhas if item.posicao.simbolo.strip().upper() == simbolo_norm
    ]
    if not correspondentes:
        return None
    if len(correspondentes) == 1:
        return ResumoCarteiraAgora.de_linha(correspondentes[0])

    quantidade = sum(item.posicao.quantidade for item in correspondentes)
    investido = sum(item.posicao.valor_investido for item in correspondentes)
    preco_medio = investido / quantidade if quantidade > 0 else 0.0
    moeda = correspondentes[0].cotacao.moeda if correspondentes[0].cotacao else "BRL"
    return ResumoCarteiraAgora(
        quantidade=quantidade,
        preco_compra=round(preco_medio, 4),
        valor_investido=round(investido, 4),
        moeda=moeda,
    )
