"""Dados de recomendacoes e movimentos de analistas sobre uma acao."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResumoOpinioesAnalistas:
    """Visao consolidada da recomendacao media e precos-alvo."""

    recomendacao_texto: str = ""
    recomendacao_media: float | None = None
    nota_media_descricao: str = ""
    quantidade_analistas: int | None = None
    preco_alvo_min: float | None = None
    preco_alvo_medio: float | None = None
    preco_alvo_max: float | None = None
    preco_alvo_mediano: float | None = None
    compra_forte: int = 0
    comprar: int = 0
    manter: int = 0
    vender: int = 0
    venda_forte: int = 0


@dataclass
class HistoricoRecomendacaoPeriodo:
    """Distribuicao de notas em um periodo (ex.: mes atual)."""

    periodo: str
    compra_forte: int
    comprar: int
    manter: int
    vender: int
    venda_forte: int


@dataclass
class MovimentoAnalista:
    """Alteracao de recomendacao publicada por uma instituicao."""

    data: str
    instituicao: str
    nota_anterior: str
    nota_nova: str
    acao: str
    preco_alvo: float | None = None
    preco_alvo_anterior: float | None = None


@dataclass
class OpinioesAnalistasPacote:
    """Pacote exibido na janela de opinioes dos analistas."""

    simbolo: str
    codigo: str
    nome_empresa: str
    moeda: str
    resumo: ResumoOpinioesAnalistas = field(default_factory=ResumoOpinioesAnalistas)
    historico: list[HistoricoRecomendacaoPeriodo] = field(default_factory=list)
    movimentos: list[MovimentoAnalista] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
