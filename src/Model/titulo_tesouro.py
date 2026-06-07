"""Modelos de titulos do Tesouro Direto."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class TituloTesouro:
    """Titulo publico federal disponivel no Tesouro Direto."""

    identificador: str
    tipo_titulo: str
    familia: str
    data_vencimento: date
    data_vencimento_texto: str
    data_base: date
    data_base_texto: str
    taxa_compra: float | None
    taxa_venda: float | None
    pu_compra: float | None
    pu_venda: float | None
    pu_base: float | None


@dataclass
class HistoricoPuTesouro:
    """Serie historica de PU para analise de volatilidade indicativa."""

    data_base_texto: str
    pu_base: float | None


@dataclass
class DetalhesTituloTesouro:
    """Dados completos de um titulo para a tela de detalhes."""

    titulo: TituloTesouro
    historico_pu: list[HistoricoPuTesouro] = field(default_factory=list)
    volatilidade_indicativa_pct: float | None = None
    amplitude_pu_pct: float | None = None


@dataclass
class PainelTesouro:
    """Lista de titulos vigentes e metadados da carga."""

    titulos: list[TituloTesouro]
    data_base_texto: str
    familias: list[str]
    aviso: str = ""
