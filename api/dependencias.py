"""Instancias compartilhadas — apenas servicos sem interface desktop."""
from __future__ import annotations

from functools import lru_cache

from src.Service.busca_acoes_servico import BuscaAcoesServico
from src.Service.busca_cripto_servico import BuscaCriptoServico
from src.Service.busca_fiis_servico import BuscaFiisServico
from src.Service.detalhes_acao_servico import DetalhesAcaoServico
from src.Service.detalhes_cripto_servico import DetalhesCriptoServico
from src.Service.mercado_cripto_servico import MercadoCriptoServico
from src.Service.mercado_fiis_servico import MercadoFiisServico
from src.Service.mercado_servico import MercadoServico


@lru_cache(maxsize=1)
def obter_mercado_servico() -> MercadoServico:
    """Cotacoes e historico (Yahoo -> Brapi -> Yahoo Chart)."""
    return MercadoServico()


@lru_cache(maxsize=1)
def obter_mercado_cripto_servico() -> MercadoCriptoServico:
    """Cotacoes e historico de criptomoedas."""
    return MercadoCriptoServico()


@lru_cache(maxsize=1)
def obter_mercado_fiis_servico() -> MercadoFiisServico:
    """Cotacoes e historico de fundos imobiliarios."""
    return MercadoFiisServico()


@lru_cache(maxsize=1)
def obter_busca_servico() -> BuscaAcoesServico:
    """Busca de tickers por nome ou codigo."""
    return BuscaAcoesServico()


@lru_cache(maxsize=1)
def obter_busca_cripto_servico() -> BuscaCriptoServico:
    """Busca de criptomoedas."""
    return BuscaCriptoServico()


@lru_cache(maxsize=1)
def obter_busca_fiis_servico() -> BuscaFiisServico:
    """Busca de fundos imobiliarios."""
    return BuscaFiisServico()


@lru_cache(maxsize=1)
def obter_detalhes_acao_servico() -> DetalhesAcaoServico:
    """Detalhes de acoes e FIIs."""
    return DetalhesAcaoServico()


@lru_cache(maxsize=1)
def obter_detalhes_cripto_servico() -> DetalhesCriptoServico:
    """Detalhes de criptomoedas."""
    return DetalhesCriptoServico()
