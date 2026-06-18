"""Resumo da posicao na carteira para a tela Agora."""
from __future__ import annotations

from dataclasses import dataclass

from src.Model.carteira import LinhaCarteira, PosicaoCarteira, TipoAtivoCarteira
from src.Service.carteira_servico import CarteiraServico


def _moeda_padrao_por_tipo(tipo: TipoAtivoCarteira) -> str:
    return "USD" if tipo == "cripto" else "BRL"


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
        moeda = linha.cotacao.moeda if linha.cotacao else _moeda_padrao_por_tipo(linha.posicao.tipo_ativo)
        return cls(
            quantidade=linha.posicao.quantidade,
            preco_compra=linha.posicao.preco_compra,
            valor_investido=linha.posicao.valor_investido,
            moeda=moeda,
        )

    @classmethod
    def de_posicao(cls, posicao: PosicaoCarteira) -> ResumoCarteiraAgora:
        return cls(
            quantidade=posicao.quantidade,
            preco_compra=posicao.preco_compra,
            valor_investido=posicao.valor_investido,
            moeda=_moeda_padrao_por_tipo(posicao.tipo_ativo),
        )


def buscar_resumo_carteira(
    simbolo: str,
    linha: LinhaCarteira | None = None,
) -> ResumoCarteiraAgora | None:
    """Retorna resumo da posicao sem buscar cotacoes na rede (leitura local)."""
    if linha is not None:
        return ResumoCarteiraAgora.de_linha(linha)

    posicoes = CarteiraServico().listar()
    if not posicoes:
        return None

    simbolo_norm = simbolo.strip().upper()
    correspondentes = [
        item for item in posicoes if item.simbolo.strip().upper() == simbolo_norm
    ]
    if not correspondentes:
        return None
    if len(correspondentes) == 1:
        return ResumoCarteiraAgora.de_posicao(correspondentes[0])

    quantidade = sum(item.quantidade for item in correspondentes)
    investido = sum(item.valor_investido for item in correspondentes)
    preco_medio = investido / quantidade if quantidade > 0 else 0.0
    moeda = _moeda_padrao_por_tipo(correspondentes[0].tipo_ativo)
    return ResumoCarteiraAgora(
        quantidade=quantidade,
        preco_compra=round(preco_medio, 4),
        valor_investido=round(investido, 4),
        moeda=moeda,
    )
