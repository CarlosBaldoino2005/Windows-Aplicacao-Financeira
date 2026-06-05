"""Instancias compartilhadas dos controladores (reuso da logica desktop)."""
from __future__ import annotations

from functools import lru_cache

from src.Controller.controlador_mercado import ControladorMercado


@lru_cache(maxsize=1)
def obter_controlador_mercado() -> ControladorMercado:
    """Uma instancia por processo para cache interno dos servicos."""
    return ControladorMercado()
