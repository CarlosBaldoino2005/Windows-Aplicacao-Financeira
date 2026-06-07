"""Botao com icone de engrenagem para abrir configuracoes."""
from __future__ import annotations

from typing import Any

import customtkinter as ctk

# Glifo Settings (engrenagem) — Segoe MDL2 Assets (Windows).
_GLIIFO_ENGRENAGEM = "\uE713"
_FONTE_ICONE = "Segoe MDL2 Assets"


def criar_botao_engrenagem(
    pai: ctk.CTkBaseClass,
    *,
    command: Any,
    fg_color: str,
    hover_color: str,
    text_color: str,
    width: int = 40,
    height: int = 40,
) -> ctk.CTkButton:
    """Botao quadrado apenas com icone de engrenagem."""
    return ctk.CTkButton(
        pai,
        text=_GLIIFO_ENGRENAGEM,
        width=width,
        height=height,
        font=ctk.CTkFont(family=_FONTE_ICONE, size=20),
        command=command,
        fg_color=fg_color,
        hover_color=hover_color,
        text_color=text_color,
        corner_radius=8,
    )
