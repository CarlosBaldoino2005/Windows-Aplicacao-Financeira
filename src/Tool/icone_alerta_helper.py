"""Botao com icone de alerta para abrir monitoramento."""
from __future__ import annotations

from typing import Any

import customtkinter as ctk

from src.View.botao_helper import estilo_botao_icone

# Glifo StatusWarning — Segoe MDL2 Assets (Windows).
_GLIIFO_ALERTA = "\uE814"
_FONTE_ICONE = "Segoe MDL2 Assets"


def criar_botao_alerta(
    pai: ctk.CTkBaseClass,
    *,
    command: Any,
    fg_color: str | None = None,
    hover_color: str | None = None,
    text_color: str | None = None,
    width: int = 40,
    height: int = 40,
) -> ctk.CTkButton:
    """Botao quadrado com icone de alerta (fundo transparente)."""
    estilo = estilo_botao_icone()
    if fg_color is not None:
        estilo["fg_color"] = fg_color
    if hover_color is not None:
        estilo["hover_color"] = hover_color
    if text_color is not None:
        estilo["text_color"] = text_color

    return ctk.CTkButton(
        pai,
        text=_GLIIFO_ALERTA,
        width=width,
        height=height,
        font=ctk.CTkFont(family=_FONTE_ICONE, size=20),
        command=command,
        corner_radius=8,
        **estilo,
    )
