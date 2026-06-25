"""Contexto do ativo na tela Agora para analises (analistas e IA)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextoAnaliseAgora:
    """Dados atuais do ativo usados nas telas de analise."""

    simbolo: str
    nome_ativo: str
    moeda: str
    tipo_ativo: str = ""
    preco_atual: float | None = None
    variacao_valor: float | None = None
    variacao_pct: float | None = None
    metricas_resumo: str = ""
    quantidade_carteira: float | None = None
    preco_compra_carteira: float | None = None
    valor_investido_carteira: float | None = None
    alerta_preco_venda: float | None = None
    alerta_preco_compra: float | None = None
