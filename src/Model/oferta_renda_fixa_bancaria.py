"""Ofertas de LCI, LCA e CDB agregadas de fontes externas (Meelion)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OfertaRendaFixaBancaria:
    """Uma oferta de renda fixa bancaria listada por agregador."""

    id: int
    nome: str
    tipo: str
    emissor: str
    distribuidor: str
    indexador: str
    taxa_rotulo: str
    percentual_cdi: float | None
    taxa_prefixada_aa: float | None
    investimento_minimo: float | None
    data_vencimento_texto: str
    dias_ate_vencimento: int | None
    taxa_liquida_aa: float | None
    taxa_bruta_aa: float | None
    url_detalhe: str


@dataclass
class ResultadoConsultaOfertas:
    """Resposta da consulta de ofertas por distribuidor."""

    ofertas: list[OfertaRendaFixaBancaria] = field(default_factory=list)
    total_retornado: int = 0
    mensagem: str = ""
    url_comparador: str | None = None
    fonte: str = "Meelion"
    disclaimer: str = ""
    atualizado_em: str = ""
