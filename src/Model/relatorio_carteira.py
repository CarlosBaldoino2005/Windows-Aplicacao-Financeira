"""Estruturas do relatorio PDF da carteira."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.Model.carteira import TipoAtivoCarteira


@dataclass(frozen=True)
class OhlcDia:
    """Resumo intradiario de um ativo."""

    abertura: float
    maxima: float
    minima: float
    fechamento: float
    horario_maxima: str
    horario_minima: str


@dataclass(frozen=True)
class LinhaRelatorioPosicao:
    """Uma linha do relatorio para posicao da carteira."""

    simbolo: str
    codigo: str
    nome: str
    tipo: TipoAtivoCarteira
    quantidade: float
    preco_compra: float
    valor_investido: float
    preco_atual: float | None
    valor_atual: float | None
    variacao_dia_pct: float | None
    resultado_reais: float | None
    resultado_pct: float | None
    moeda: str
    ohlc_dia: OhlcDia | None = None


@dataclass(frozen=True)
class LinhaRelatorioMercado:
    """Ativo em alta ou queda no mercado."""

    simbolo: str
    codigo: str
    nome: str
    preco: float
    variacao_pct: float
    variacao_valor: float
    moeda: str
    ohlc_dia: OhlcDia | None = None


@dataclass(frozen=True)
class ResumoRelatorioCarteira:
    """Totais consolidados da carteira."""

    total_investido: float
    total_atual: float
    resultado_reais: float
    resultado_pct: float
    total_dividendos: float
    dividendo_previsto_mes: float


@dataclass
class DadosRelatorioCarteira:
    """Pacote completo para gerar o PDF."""

    gerado_em: str
    resumo: ResumoRelatorioCarteira
    posicoes: list[LinhaRelatorioPosicao] = field(default_factory=list)
    acoes_em_alta: list[LinhaRelatorioMercado] = field(default_factory=list)
    acoes_em_queda: list[LinhaRelatorioMercado] = field(default_factory=list)
    fiis_em_alta: list[LinhaRelatorioMercado] = field(default_factory=list)
    fiis_em_queda: list[LinhaRelatorioMercado] = field(default_factory=list)
    etfs_em_alta: list[LinhaRelatorioMercado] = field(default_factory=list)
    etfs_em_queda: list[LinhaRelatorioMercado] = field(default_factory=list)
    cripto_em_alta: list[LinhaRelatorioMercado] = field(default_factory=list)
    cripto_em_queda: list[LinhaRelatorioMercado] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
