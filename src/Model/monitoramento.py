"""Registro de monitoramento de precos por ativo."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.Model.cotacao import CotacaoResumo

TipoAtivoMonitoramento = Literal["acoes", "cripto", "fiis", "dividendos"]
StatusMonitoramento = Literal["normal", "abaixo", "acima", "indisponivel", "pausado"]

TIPOS_ATIVO_MONITORAMENTO: tuple[TipoAtivoMonitoramento, ...] = (
    "acoes",
    "cripto",
    "fiis",
    "dividendos",
)

ROTULOS_TIPO_ATIVO: dict[TipoAtivoMonitoramento, str] = {
    "acoes": "Acao",
    "cripto": "Criptomoeda",
    "fiis": "Fundo imobiliario",
    "dividendos": "Dividendos",
}

ROTULOS_STATUS: dict[StatusMonitoramento, str] = {
    "normal": "Normal",
    "abaixo": "Abaixo do limite",
    "acima": "Acima do limite",
    "indisponivel": "Sem cotacao",
    "pausado": "Pausado",
}

MAXIMO_ITENS_MONITORAMENTO = 100


@dataclass(frozen=True)
class MonitoramentoItem:
    """Limite de preco configurado pelo usuario para um ativo."""

    id: str
    simbolo: str
    tipo_ativo: TipoAtivoMonitoramento
    valor_baixo: float | None
    valor_alto: float | None
    pausado: bool = False


@dataclass(frozen=True)
class MonitoramentoLinha:
    """Item de monitoramento com cotacao atual e status visual."""

    item: MonitoramentoItem
    cotacao: CotacaoResumo | None
    status: StatusMonitoramento


def calcular_status_monitoramento(
    preco: float | None,
    valor_baixo: float | None,
    valor_alto: float | None,
    *,
    pausado: bool = False,
) -> StatusMonitoramento:
    """Define cor da linha: vermelho abaixo do limite, verde acima, cinza se pausado."""
    if pausado:
        return "pausado"
    if preco is None or preco <= 0:
        return "indisponivel"
    if valor_baixo is not None and preco <= valor_baixo:
        return "abaixo"
    if valor_alto is not None and preco >= valor_alto:
        return "acima"
    return "normal"
