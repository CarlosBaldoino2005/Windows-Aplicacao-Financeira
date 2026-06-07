"""Fabrica de botoes — padrao unico azul (primaria) em todo o projeto."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from src.View.tema import CORES

ALTURA_BOTAO_PADRAO = 36


def _texto_inverso() -> str:
    return CORES.get("textoInverso", "#FFFFFF")


def estilo_botao_padrao(**extras: Any) -> dict[str, Any]:
    """Estilo unico: fundo azul primaria, texto claro, hover mais escuro."""
    estilo: dict[str, Any] = {
        "fg_color": CORES["primaria"],
        "hover_color": CORES["primariaHover"],
        "text_color": _texto_inverso(),
        "height": ALTURA_BOTAO_PADRAO,
        "border_width": 0,
    }
    estilo.update(extras)
    return estilo


def estilo_botao_icone(**extras: Any) -> dict[str, Any]:
    """Botao somente icone: fundo transparente, glifo azul, hover suave."""
    estilo: dict[str, Any] = {
        "fg_color": "transparent",
        "hover_color": CORES["zebraEscura"],
        "text_color": CORES["primaria"],
        "border_width": 0,
    }
    estilo.update(extras)
    return estilo


# Aliases semanticos — todos usam o mesmo azul.
estilo_botao_primario = estilo_botao_padrao
estilo_botao_secundario = estilo_botao_padrao
estilo_botao_perigo = estilo_botao_padrao


def criar_botao(
    pai: ctk.CTkBaseClass,
    texto: str,
    command: Callable[..., None] | None = None,
    **kwargs: Any,
) -> ctk.CTkButton:
    return ctk.CTkButton(pai, text=texto, command=command, **estilo_botao_padrao(**kwargs))


def criar_botao_primario(
    pai: ctk.CTkBaseClass,
    texto: str,
    command: Callable[..., None] | None = None,
    **kwargs: Any,
) -> ctk.CTkButton:
    return criar_botao(pai, texto, command, **kwargs)


def criar_botao_secundario(
    pai: ctk.CTkBaseClass,
    texto: str,
    command: Callable[..., None] | None = None,
    **kwargs: Any,
) -> ctk.CTkButton:
    return criar_botao(pai, texto, command, **kwargs)


def criar_botao_perigo(
    pai: ctk.CTkBaseClass,
    texto: str,
    command: Callable[..., None] | None = None,
    **kwargs: Any,
) -> ctk.CTkButton:
    return criar_botao(pai, texto, command, **kwargs)
