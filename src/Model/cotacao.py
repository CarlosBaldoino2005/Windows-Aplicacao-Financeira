"""Modelos de dados do mercado financeiro."""
from dataclasses import dataclass


@dataclass
class CotacaoResumo:
    """Resumo de uma acao para listagens e cards."""

    simbolo: str
    nome: str
    preco: float
    variacao_percentual: float
    variacao_valor: float
    volume: int | None
    moeda: str


@dataclass
class PontoHistorico:
    """Um ponto da serie historica para graficos."""

    data_iso: str
    data_exibicao: str
    preco_fechamento: float
    preco_abertura: float | None
    volume: int | None


@dataclass
class SerieHistorica:
    """Serie completa para um periodo."""

    simbolo: str
    periodo: str
    pontos: list[PontoHistorico]
