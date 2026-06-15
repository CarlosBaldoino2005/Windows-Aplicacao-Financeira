"""Opcoes de geracao automatica do relatorio PDF da carteira."""
from __future__ import annotations

from dataclasses import dataclass

RELATORIO_AUTOMATICO_HABILITADO_PADRAO = False
RELATORIO_AUTOMATICO_HORARIOS_PADRAO: tuple[str, ...] = ("18:00",)
MAXIMO_HORARIOS_RELATORIO = 24
MAXIMO_EMAILS_RELATORIO = 20


@dataclass(frozen=True)
class OpcoesRelatorioAutomaticoCarteira:
    """Relatorio PDF agendado por horarios fixos (formato HH:MM)."""

    habilitado: bool
    horarios: tuple[str, ...]
    emails_destinatarios: tuple[str, ...] = ()
