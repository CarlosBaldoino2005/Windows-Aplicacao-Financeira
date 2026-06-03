"""Tabelas zebradas com destaque azul ao passar o mouse (tela Mais detalhes)."""
from __future__ import annotations

import customtkinter as ctk

from src.View.tema import CORES


def adicionar_cabecalho_tabela(pai: ctk.CTkFrame, colunas: list[str]) -> None:
    """Cabecalho neutro (sem zebrado), no padrao global de grids."""
    linha = ctk.CTkFrame(pai, fg_color=CORES["primaria"], corner_radius=6)
    linha.pack(fill="x", padx=2, pady=(2, 0))

    for indice, texto in enumerate(colunas):
        linha.columnconfigure(indice, weight=1)
        ctk.CTkLabel(
            linha,
            text=texto,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=CORES["textoInverso"],
        ).grid(row=0, column=indice, padx=8, pady=6, sticky="w")


def adicionar_linha_zebrada(
    pai: ctk.CTkFrame,
    valores: list[str],
    indice_linha: int,
    cores_celulas: list[str] | None = None,
    largura_wrap: int = 160,
) -> ctk.CTkFrame:
    """Linha alternada branco/cinza; hover deixa fundo azul e texto branco."""
    fundo_base = CORES["zebraClara"] if indice_linha % 2 == 0 else CORES["zebraEscura"]
    linha = ctk.CTkFrame(pai, fg_color=fundo_base, corner_radius=4, height=36)
    linha.pack(fill="x", padx=2, pady=1)

    rotulos: list[ctk.CTkLabel] = []
    cores_base: list[str] = []

    for indice, texto in enumerate(valores):
        linha.columnconfigure(indice, weight=1)
        cor_texto = cores_celulas[indice] if cores_celulas and indice < len(cores_celulas) else CORES["texto"]
        cores_base.append(cor_texto)
        rotulo = ctk.CTkLabel(
            linha,
            text=texto,
            font=ctk.CTkFont(size=11),
            text_color=cor_texto,
            wraplength=largura_wrap,
            justify="left",
        )
        rotulo.grid(row=0, column=indice, padx=8, pady=6, sticky="w")
        rotulos.append(rotulo)

    _configurar_hover_linha(linha, rotulos, fundo_base, cores_base)
    return linha


def _configurar_hover_linha(
    linha: ctk.CTkFrame,
    rotulos: list[ctk.CTkLabel],
    fundo_base: str,
    cores_base: list[str],
) -> None:
    """Destaque azul na linha inteira ao passar o mouse (padrao global de grid)."""

    def ao_entrar(_evento=None) -> None:
        linha.configure(fg_color=CORES["selecao"])
        for rotulo in rotulos:
            rotulo.configure(text_color=CORES["selecaoTexto"])

    def ao_sair(_evento=None) -> None:
        linha.configure(fg_color=fundo_base)
        for rotulo, cor in zip(rotulos, cores_base, strict=True):
            rotulo.configure(text_color=cor)

    for widget in (linha, *rotulos):
        widget.bind("<Enter>", ao_entrar)
        widget.bind("<Leave>", ao_sair)
