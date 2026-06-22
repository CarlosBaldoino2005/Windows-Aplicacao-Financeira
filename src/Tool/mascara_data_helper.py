"""Mascara de entrada para data no formato pt-BR (dd/mm/aaaa)."""
from __future__ import annotations

import customtkinter as ctk


def _extrair_digitos_data(texto: str) -> str:
    return "".join(caractere for caractere in str(texto or "") if caractere.isdigit())[:8]


def formatar_digitos_data_ptbr(digitos: str) -> str:
    """Formata ate 8 digitos como dd/mm/aaaa."""
    numeros = _extrair_digitos_data(digitos)
    if not numeros:
        return ""
    if len(numeros) <= 2:
        return numeros
    if len(numeros) <= 4:
        return f"{numeros[:2]}/{numeros[2:]}"
    return f"{numeros[:2]}/{numeros[2:4]}/{numeros[4:]}"


def _tecla_permitida_mascara_data(evento) -> str | None:
    if evento.keysym in ("BackSpace", "Delete", "Left", "Right", "Home", "End", "Tab"):
        return None
    if evento.state & 0x4 and evento.keysym.lower() in ("a", "c", "v", "x"):
        return None
    if evento.char and evento.char.isdigit():
        return None
    if evento.keysym == "Return":
        return None
    return "break"


def aplicar_mascara_data_ptbr(entry: ctk.CTkEntry) -> None:
    """
    Aplica mascara dd/mm/aaaa enquanto o usuario digita.
    Aceita apenas numeros; as barras sao inseridas automaticamente.
    """

    def ao_soltar_tecla(_evento=None) -> None:
        if getattr(entry, "_mascara_pausada", False):
            return
        digitos = _extrair_digitos_data(entry.get())
        texto = formatar_digitos_data_ptbr(digitos)
        entry.delete(0, "end")
        if texto:
            entry.insert(0, texto)
        entry.icursor("end")

    entry.bind("<KeyPress>", _tecla_permitida_mascara_data, add=True)
    entry.bind("<KeyRelease>", ao_soltar_tecla, add=True)
