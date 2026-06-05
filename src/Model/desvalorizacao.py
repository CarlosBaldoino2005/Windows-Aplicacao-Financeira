"""Modelo para eventos de queda de preco dentro de um periodo."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EventoDesvalorizacao:
    """Queda do pico ao fundo antes de um novo topo ou fim do periodo."""

    data_pico: str
    data_fundo: str
    preco_pico: float
    preco_fundo: float
    variacao_percentual: float
    variacao_valor: float
    pregões: int


@dataclass
class AnaliseDesvalorizacao:
    """Resultado da analise de quedas no historico do periodo."""

    simbolo: str
    codigo_exibicao: str
    periodo_rotulo: str
    moeda: str
    eventos: list[EventoDesvalorizacao]

    @property
    def ultima(self) -> EventoDesvalorizacao | None:
        if not self.eventos:
            return None
        return self.eventos[-1]
