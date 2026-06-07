"""Componentes visuais para exibir prazo legivel (dias + anos/meses/dias)."""
from __future__ import annotations

import customtkinter as ctk

from src.Tool.formatar_prazo_helper import PrazoLegivel
from src.View.tema import CORES


def adicionar_linha_prazo_legivel(
    pai: ctk.CTkFrame,
    rotulo: str,
    prazo: PrazoLegivel,
) -> None:
    """Linha com titulo em negrito (dias) e descricao abaixo."""
    linha = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=8)
    linha.pack(fill="x", padx=4, pady=2)

    ctk.CTkLabel(
        linha,
        text=rotulo,
        font=ctk.CTkFont(size=13),
        text_color=CORES["textoSecundario"],
        width=180,
        anchor="w",
    ).pack(side="left", padx=12, pady=8)

    coluna = ctk.CTkFrame(linha, fg_color="transparent")
    coluna.pack(side="left", fill="x", expand=True, padx=8, pady=8)

    ctk.CTkLabel(
        coluna,
        text=prazo.titulo,
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=CORES["texto"],
        anchor="w",
        justify="left",
    ).pack(anchor="w")

    ctk.CTkLabel(
        coluna,
        text=prazo.descricao,
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
        anchor="w",
        justify="left",
    ).pack(anchor="w", pady=(2, 0))

    if prazo.intervalo:
        ctk.CTkLabel(
            coluna,
            text=prazo.intervalo,
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            anchor="w",
            justify="left",
        ).pack(anchor="w", pady=(2, 0))
