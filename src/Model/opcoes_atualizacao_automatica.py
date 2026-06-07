"""Opcoes globais de atualizacao automatica de cotacoes."""
from __future__ import annotations

from dataclasses import dataclass

# Padrao: desligado; quando ligado, intervalo inicial de 60 s (nao 5 s).
ATUALIZACAO_AUTOMATICA_HABILITADA_PADRAO = False
INTERVALO_PADRAO_SEGUNDOS = 60
INTERVALO_MINIMO_SEGUNDOS = 10
INTERVALO_MAXIMO_SEGUNDOS = 3600


@dataclass(frozen=True)
class OpcoesAtualizacaoAutomatica:
    """Atualizacao periodica compartilhada por paineis de cotacoes."""

    habilitada: bool
    intervalo_segundos: int
