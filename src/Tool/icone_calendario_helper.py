"""Botao com icone de calendario para selecao de data."""
from __future__ import annotations

from typing import Any

import customtkinter as ctk

from src.View.botao_helper import estilo_botao_icone

_GLIIFO_CALENDARIO = "\uE787"
_FONTE_ICONE = "Segoe MDL2 Assets"


def criar_botao_calendario(
    pai: ctk.CTkBaseClass,
    *,
    command: Any,
    fg_color: str | None = None,
    hover_color: str | None = None,
    text_color: str | None = None,
    width: int = 32,
    height: int = 28,
) -> ctk.CTkButton:
    """Botao compacto com icone de calendario (Segoe MDL2 Assets)."""
    estilo = estilo_botao_icone()
    if fg_color is not None:
        estilo["fg_color"] = fg_color
    if hover_color is not None:
        estilo["hover_color"] = hover_color
    if text_color is not None:
        estilo["text_color"] = text_color

    return ctk.CTkButton(
        pai,
        text=_GLIIFO_CALENDARIO,
        width=width,
        height=height,
        font=ctk.CTkFont(family=_FONTE_ICONE, size=16),
        command=command,
        corner_radius=8,
        **estilo,
    )
