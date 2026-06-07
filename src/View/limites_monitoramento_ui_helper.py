"""Utilitarios compartilhados para campos de limite de monitoramento."""
from __future__ import annotations

import customtkinter as ctk

from src.Tool.mascara_moeda_helper import formatar_centavos_ptbr


def valor_para_campo_moeda(valor: float | None) -> str:
    if valor is None or valor <= 0:
        return ""
    centavos = int(round(valor * 100))
    return f"R$ {formatar_centavos_ptbr(centavos)}"


def preencher_entrada_moeda(entry: ctk.CTkEntry, valor: float | None) -> None:
    """Substitui o texto do campo com valor formatado em pt-BR."""
    entry.delete(0, "end")
    texto = valor_para_campo_moeda(valor)
    if texto:
        entry.insert(0, texto)
