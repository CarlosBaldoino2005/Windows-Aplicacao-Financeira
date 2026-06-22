"""Registro de negociacao exibido na tela Negocios do Agora."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TendenciaNegocio = Literal["alta", "baixa", "neutra"]
LadoNegocio = Literal["compra", "venda", "neutro"]


@dataclass(frozen=True)
class NegocioAgora:
    """Uma linha da fita de negocios no padrao ADVFN."""

    id: str
    hora: str
    preco: float
    tamanho: int
    tipo: str
    lado: LadoNegocio
    preco_compra: float | None
    preco_venda: float | None
    total_volume: int
    numero: int
    bolsa: str
    tendencia: TendenciaNegocio


@dataclass(frozen=True)
class ResumoNegociosAgora:
    """Totais por lado para a barra Comprar / Neutro / Vender."""

    compra: int
    neutro: int
    venda: int

    @property
    def total(self) -> int:
        return self.compra + self.neutro + self.venda
