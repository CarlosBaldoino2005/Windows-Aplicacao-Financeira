"""Grid padrao de cotacoes (zebrada) reutilizada no painel e em favoritos."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from src.Model.cotacao import CotacaoResumo
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.tema import CORES


def criar_card_tabela(
    pai: ctk.CTkFrame,
    titulo: str,
    altura: int = 8,
    ao_duplo_clique: Callable | None = None,
    expandir: bool = False,
) -> ttk.Treeview:
    """Monta card com Treeview no mesmo estilo do painel principal."""
    card = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=12)
    if expandir:
        card.pack(fill="both", expand=True, pady=8)
    else:
        card.pack(fill="x", pady=8)

    ctk.CTkLabel(
        card,
        text=titulo,
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=CORES["texto"],
    ).pack(anchor="w", padx=12, pady=(12, 4))

    frame_tabela = tk.Frame(card, bg=CORES["superficie"])
    frame_tabela.pack(fill="both", expand=expandir, padx=12, pady=(0, 12))

    colunas = ("simbolo", "nome", "preco", "variacao")
    tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=altura)
    tabela.heading("simbolo", text="Acao")
    tabela.heading("nome", text="Nome")
    tabela.heading("preco", text="Preco")
    tabela.heading("variacao", text="Variacao")
    tabela.column("simbolo", width=90)
    tabela.column("nome", width=220)
    tabela.column("preco", width=120)
    tabela.column("variacao", width=180)

    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure(
        "Treeview",
        background=CORES["zebraClara"],
        fieldbackground=CORES["zebraClara"],
        foreground=CORES["texto"],
        rowheight=28,
    )
    estilo.configure("Treeview.Heading", background="#E2E8F0", font=("Segoe UI", 10, "bold"))
    tabela.tag_configure("par", background=CORES["zebraClara"])
    tabela.tag_configure("impar", background=CORES["zebraEscura"])
    tabela.tag_configure("selecionado", background=CORES["selecao"], foreground=CORES["selecaoTexto"])

    tabela.pack(fill="both", expand=expandir)
    if ao_duplo_clique:
        tabela.bind("<Double-1>", ao_duplo_clique)

    return tabela


def preencher_tabela(tabela: ttk.Treeview, itens: list[CotacaoResumo]) -> None:
    """Preenche linhas com cotacao formatada em pt-BR."""
    for linha in tabela.get_children():
        tabela.delete(linha)

    for i, item in enumerate(itens):
        tag = "par" if i % 2 == 0 else "impar"
        tabela.insert(
            "",
            "end",
            iid=item.simbolo,
            values=(
                item.simbolo.replace(".SA", ""),
                item.nome,
                formatar_moeda(item.preco, item.moeda),
                formatar_variacao(item.variacao_valor, item.variacao_percentual, item.moeda),
            ),
            tags=(tag,),
        )
