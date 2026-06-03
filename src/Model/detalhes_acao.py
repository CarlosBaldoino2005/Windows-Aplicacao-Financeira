"""Modelos para tela de detalhes fundamentais da acao."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PeriodoResultado:
    """Receita e lucro em um trimestre ou ano."""

    periodo: str
    receita: float | None = None
    lucro_liquido: float | None = None
    ebitda: float | None = None
    lucro_operacional: float | None = None


@dataclass
class LinhaDemonstrativo:
    """Uma linha da DRE/balanco/fluxo com valores por periodo."""

    rotulo: str
    valores: dict[str, float] = field(default_factory=dict)


@dataclass
class PagamentoDividendo:
    """Um pagamento de dividendo por acao."""

    data_pagamento: str
    valor_por_cota: float
    data_iso: str = ""


@dataclass
class ConcorrenteResumo:
    """Resumo financeiro de um concorrente."""

    codigo: str
    nome: str
    moeda: str
    lucro_liquido: float | None = None
    margem_lucro: float | None = None
    receita: float | None = None
    capitalizacao: float | None = None
    preco_atual: float | None = None
    variacao_dia_pct: float | None = None


@dataclass
class DetalhesAcao:
    """Pacote completo exibido na janela Mais detalhes."""

    simbolo: str
    codigo: str
    moeda: str
    nome_empresa: str
    setor: str = ""
    industria: str = ""
    pais: str = ""
    site: str = ""
    descricao: str = ""
    funcionarios: int | None = None
    preco_atual: float | None = None
    variacao_dia_pct: float | None = None
    indicadores: list[tuple[str, str]] = field(default_factory=list)
    trimestres: list[PeriodoResultado] = field(default_factory=list)
    anuais: list[PeriodoResultado] = field(default_factory=list)
    dre_trimestral: list[LinhaDemonstrativo] = field(default_factory=list)
    dre_anual: list[LinhaDemonstrativo] = field(default_factory=list)
    balanco: list[LinhaDemonstrativo] = field(default_factory=list)
    fluxo_caixa: list[LinhaDemonstrativo] = field(default_factory=list)
    concorrentes: list[ConcorrenteResumo] = field(default_factory=list)
    pagamentos_dividendos: list[PagamentoDividendo] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    eh_cripto: bool = False
