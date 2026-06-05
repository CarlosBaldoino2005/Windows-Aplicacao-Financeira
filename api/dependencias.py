"""Instancias compartilhadas — apenas servicos sem interface desktop."""
from __future__ import annotations

from functools import lru_cache

from src.Service.busca_acoes_servico import BuscaAcoesServico
from src.Service.mercado_servico import MercadoServico


@lru_cache(maxsize=1)
def obter_mercado_servico() -> MercadoServico:
    """Cotacoes e historico (Yahoo -> Brapi -> Yahoo Chart)."""
    return MercadoServico()


@lru_cache(maxsize=1)
def obter_busca_servico() -> BuscaAcoesServico:
    """Busca de tickers por nome ou codigo."""
    return BuscaAcoesServico()
