"""Tabelas zebradas com destaque azul ao passar o mouse (tela Mais detalhes)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Model.opcoes_fonte_grid import OpcoesFonteGrid
from src.Tool.config_painel import ConfigPainelIni
from src.View.grid_ordenacao_helper import (
    EstadoOrdenacaoColuna,
    LinhaTabelaOrdenavel,
    ordenar_linhas_tabela,
    titulo_coluna_ordenada,
)
from src.View.tema import CORES


def _resolver_opcoes(opcoes: OpcoesFonteGrid | None) -> OpcoesFonteGrid:
    if opcoes is not None:
        return opcoes
    return ConfigPainelIni().carregar_opcoes_fonte_grid()


def adicionar_cabecalho_tabela(
    pai: ctk.CTkFrame,
    colunas: list[str],
    opcoes_fonte: OpcoesFonteGrid | None = None,
    estado_ordenacao: EstadoOrdenacaoColuna | None = None,
    ao_clicar_coluna: Callable[[int], None] | None = None,
) -> None:
    """Cabecalho neutro; clique na coluna ordena quando estado_ordenacao e callback forem informados."""
    opcoes = _resolver_opcoes(opcoes_fonte)
    linha = ctk.CTkFrame(pai, fg_color=CORES["primaria"], corner_radius=6)
    linha.pack(fill="x", padx=2, pady=(2, 0))

    for indice, texto in enumerate(colunas):
        linha.columnconfigure(indice, weight=1)
        rotulo_texto = titulo_coluna_ordenada(texto, indice, estado_ordenacao)
        rotulo = ctk.CTkLabel(
            linha,
            text=rotulo_texto,
            font=ctk.CTkFont(size=opcoes.fonte_cabecalho_ctk, weight="bold"),
            text_color=CORES["textoInverso"],
        )
        rotulo.grid(row=0, column=indice, padx=8, pady=opcoes.padding_celula_y, sticky="w")
        if ao_clicar_coluna is not None:
            indice_coluna = indice

            def _clicar(_evento=None, coluna=indice_coluna) -> None:
                ao_clicar_coluna(coluna)

            rotulo.bind("<Button-1>", _clicar, add="+")
            try:
                rotulo.configure(cursor="hand2")
            except Exception:
                pass


def renderizar_tabela_zebrada(
    pai: ctk.CTkFrame,
    colunas: list[str],
    linhas: list[LinhaTabelaOrdenavel],
    estado_ordenacao: EstadoOrdenacaoColuna,
    ao_mudar_ordenacao: Callable[[], None],
    opcoes_fonte: OpcoesFonteGrid | None = None,
    largura_wrap: int | None = None,
) -> None:
    """Desenha cabecalho ordenavel e linhas zebradas ja ordenadas."""

    def _clicar_coluna(indice: int) -> None:
        estado_ordenacao.alternar(indice)
        ao_mudar_ordenacao()

    adicionar_cabecalho_tabela(
        pai,
        colunas,
        opcoes_fonte,
        estado_ordenacao,
        _clicar_coluna,
    )
    linhas_ordenadas = ordenar_linhas_tabela(linhas, estado_ordenacao)
    for indice, linha in enumerate(linhas_ordenadas):
        adicionar_linha_zebrada(
            pai,
            linha.valores,
            indice,
            cores_celulas=linha.cores_celulas,
            largura_wrap=largura_wrap,
            opcoes_fonte=opcoes_fonte,
            ao_duplo_clique=linha.ao_duplo_clique,
        )


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
    contador = {"valor": 0}

    def aplicar_hover() -> None:
        linha.configure(fg_color=CORES["selecao"])
        for rotulo in rotulos:
            rotulo.configure(text_color=CORES["selecaoTexto"])

    def remover_hover() -> None:
        linha.configure(fg_color=fundo_base)
        for rotulo, cor in zip(rotulos, cores_base, strict=True):
            rotulo.configure(text_color=cor)

    def ao_entrar(_evento=None) -> None:
        contador["valor"] += 1
        if contador["valor"] == 1:
            aplicar_hover()

    def ao_sair(_evento=None) -> None:
        contador["valor"] -= 1
        if contador["valor"] <= 0:
            contador["valor"] = 0
            remover_hover()

    for widget in (linha, *rotulos):
        widget.bind("<Enter>", ao_entrar, add="+")
        widget.bind("<Leave>", ao_sair, add="+")
