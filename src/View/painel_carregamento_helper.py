"""Painel visual de carregamento para janelas que buscam dados em thread."""
from __future__ import annotations

import customtkinter as ctk

from src.View.tema import CORES


def montar_painel_carregamento(
    pai: ctk.CTkFrame,
    *,
    titulo: str,
    detalhe: str = "Aguarde enquanto buscamos as informacoes.",
) -> tuple[ctk.CTkFrame, ctk.CTkProgressBar, ctk.CTkLabel]:
    """Monta card central com barra de progresso e texto de espera."""
    card = ctk.CTkFrame(
        pai,
        fg_color=CORES["superficie"],
        corner_radius=12,
        border_width=1,
        border_color=CORES["borda"],
    )
    card.pack(fill="both", expand=True, padx=8, pady=8)

    centro = ctk.CTkFrame(card, fg_color="transparent")
    centro.place(relx=0.5, rely=0.45, anchor="center")

    ctk.CTkLabel(
        centro,
        text=titulo,
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=CORES["texto"],
    ).pack(pady=(0, 12))

    barra = ctk.CTkProgressBar(centro, width=320, mode="indeterminate")
    barra.pack(pady=(0, 12))
    barra.start()

    label_detalhe = ctk.CTkLabel(
        centro,
        text=detalhe,
        font=ctk.CTkFont(size=13),
        text_color=CORES["textoSecundario"],
        wraplength=520,
        justify="center",
    )
    label_detalhe.pack()

    return card, barra, label_detalhe


def parar_painel_carregamento(barra: ctk.CTkProgressBar | None) -> None:
    """Interrompe a animacao da barra antes de remover o painel."""
    if barra is None:
        return
    try:
        barra.stop()
    except Exception:
        pass
