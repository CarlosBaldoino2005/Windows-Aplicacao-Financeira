"""Tabelas zebradas com destaque azul ao passar o mouse (tela Mais detalhes)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Model.opcoes_fonte_grid import OpcoesFonteGrid
from src.Tool.config_painel import ConfigPainelIni
from src.View.tema import CORES


def _resolver_opcoes(opcoes: OpcoesFonteGrid | None) -> OpcoesFonteGrid:
    if opcoes is not None:
        return opcoes
    return ConfigPainelIni().carregar_opcoes_fonte_grid()


def adicionar_cabecalho_tabela(
    pai: ctk.CTkFrame,
    colunas: list[str],
    opcoes_fonte: OpcoesFonteGrid | None = None,
) -> None:
    """Cabecalho neutro (sem zebrado), no padrao global de grids."""
    opcoes = _resolver_opcoes(opcoes_fonte)
    linha = ctk.CTkFrame(pai, fg_color=CORES["primaria"], corner_radius=6)
    linha.pack(fill="x", padx=2, pady=(2, 0))

    for indice, texto in enumerate(colunas):
        linha.columnconfigure(indice, weight=1)
        ctk.CTkLabel(
            linha,
            text=texto,
            font=ctk.CTkFont(size=opcoes.fonte_cabecalho_ctk, weight="bold"),
            text_color=CORES["textoInverso"],
        ).grid(row=0, column=indice, padx=8, pady=opcoes.padding_celula_y, sticky="w")


def adicionar_linha_zebrada(
    pai: ctk.CTkFrame,
    valores: list[str],
    indice_linha: int,
    cores_celulas: list[str] | None = None,
    largura_wrap: int | None = None,
    opcoes_fonte: OpcoesFonteGrid | None = None,
    ao_duplo_clique: Callable | None = None,
) -> ctk.CTkFrame:
    """Linha alternada branco/cinza; hover deixa fundo azul e texto branco."""
    opcoes = _resolver_opcoes(opcoes_fonte)
    wrap = largura_wrap if largura_wrap is not None else opcoes.largura_wrap
    fundo_base = CORES["zebraClara"] if indice_linha % 2 == 0 else CORES["zebraEscura"]
    altura_min = opcoes.altura_linha - 4
    linha = ctk.CTkFrame(pai, fg_color=fundo_base, corner_radius=4, height=altura_min)
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
            font=ctk.CTkFont(size=opcoes.fonte_celula),
            text_color=cor_texto,
            wraplength=wrap,
            justify="left",
        )
        rotulo.grid(row=0, column=indice, padx=8, pady=opcoes.padding_celula_y, sticky="w")
        rotulos.append(rotulo)

    _configurar_hover_linha(linha, rotulos, fundo_base, cores_base)

    if ao_duplo_clique is not None:
        for widget in (linha, *rotulos):
            widget.bind("<Double-1>", lambda _e: ao_duplo_clique(), add="+")
            try:
                widget.configure(cursor="hand2")
            except Exception:
                pass

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
