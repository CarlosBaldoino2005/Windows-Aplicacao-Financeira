"""Grid padrao de cotacoes (zebrada) reutilizada no painel e em favoritos."""
from __future__ import annotations

from collections.abc import Callable, Iterable

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from src.Model.cotacao import CotacaoResumo
from src.Model.opcoes_fonte_grid import OpcoesFonteGrid
from src.Tool.config_painel import ConfigPainelIni
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.tema import CORES

_COLUNAS_PADRAO = ("simbolo", "nome", "preco", "variacao")
_FONTE_FAMILIA = "Segoe UI"


def _resolver_opcoes(opcoes: OpcoesFonteGrid | None) -> OpcoesFonteGrid:
    if opcoes is not None:
        return opcoes
    return ConfigPainelIni().carregar_opcoes_fonte_grid()


def definir_rotulo_coluna_variacao(tabela: ttk.Treeview, rotulo: str) -> None:
    """Altera o cabecalho da coluna de variacao (ex.: periodo selecionado)."""
    tabela.heading("variacao", text=rotulo)


def criar_card_tabela(
    pai: ctk.CTkFrame,
    titulo: str,
    altura: int = 8,
    ao_duplo_clique: Callable | None = None,
    expandir: bool = False,
    opcoes_fonte: OpcoesFonteGrid | None = None,
) -> ttk.Treeview:
    """Monta card com Treeview no mesmo estilo do painel principal."""
    opcoes = _resolver_opcoes(opcoes_fonte)
    card = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=12)
    if expandir:
        card.pack(fill="both", expand=True, pady=8)
    else:
        card.pack(fill="x", pady=8)

    label_titulo = ctk.CTkLabel(
        card,
        text=titulo,
        font=ctk.CTkFont(size=opcoes.fonte_titulo_card, weight="bold"),
        text_color=CORES["texto"],
    )
    label_titulo.pack(anchor="w", padx=12, pady=(12, 4))

    frame_tabela = tk.Frame(card, bg=CORES["superficie"])
    frame_tabela.pack(fill="both", expand=expandir, padx=12, pady=(0, 12))

    tabela = ttk.Treeview(frame_tabela, columns=_COLUNAS_PADRAO, show="headings", height=altura)
    tabela.heading("simbolo", text="Acao")
    tabela.heading("nome", text="Nome")
    tabela.heading("preco", text="Preco")
    tabela.heading("variacao", text="Variacao")

    tabela.pack(fill="both", expand=expandir)
    aplicar_estilo_tabela(tabela, opcoes)
    if ao_duplo_clique:
        tabela.bind("<Double-1>", ao_duplo_clique)

    label_vazio = ctk.CTkLabel(
        card,
        text="",
        font=ctk.CTkFont(size=opcoes.fonte_mensagem_vazio),
        text_color=CORES["textoSecundario"],
        wraplength=900,
        justify="left",
    )
    label_vazio.pack(fill="x", padx=12, pady=(0, 12))
    label_vazio.pack_forget()
    tabela._card_pai = card  # type: ignore[attr-defined]
    tabela._label_vazio = label_vazio  # type: ignore[attr-defined]
    tabela._label_titulo_card = label_titulo  # type: ignore[attr-defined]

    return tabela


def aplicar_estilo_tabela(
    tabela: ttk.Treeview,
    opcoes_fonte: OpcoesFonteGrid | None = None,
) -> None:
    """Atualiza cores e fonte da grid (chamar apos trocar tema ou tamanho no INI)."""
    opcoes = _resolver_opcoes(opcoes_fonte)
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure(
        "Treeview",
        background=CORES["zebraClara"],
        fieldbackground=CORES["zebraClara"],
        foreground=CORES["texto"],
        rowheight=opcoes.altura_linha,
        font=(_FONTE_FAMILIA, opcoes.fonte_tree),
    )
    estilo.configure(
        "Treeview.Heading",
        background=CORES["zebraEscura"],
        foreground=CORES["texto"],
        font=(_FONTE_FAMILIA, opcoes.fonte_cabecalho_tree, "bold"),
    )
    tabela.tag_configure("par", background=CORES["zebraClara"])
    tabela.tag_configure("impar", background=CORES["zebraEscura"])
    tabela.tag_configure("selecionado", background=CORES["selecao"], foreground=CORES["selecaoTexto"])

    larguras = opcoes.larguras_colunas
    for coluna, largura in zip(_COLUNAS_PADRAO, larguras, strict=True):
        tabela.column(coluna, width=largura)

    label_titulo = getattr(tabela, "_label_titulo_card", None)
    if label_titulo is not None:
        label_titulo.configure(font=ctk.CTkFont(size=opcoes.fonte_titulo_card, weight="bold"))

    label_vazio = getattr(tabela, "_label_vazio", None)
    if label_vazio is not None:
        label_vazio.configure(font=ctk.CTkFont(size=opcoes.fonte_mensagem_vazio))


def reaplicar_fonte_em_tabelas(tabelas: Iterable[ttk.Treeview]) -> None:
    """Reaplica fonte/colunas apos mudar pequeno/medio/grande no INI."""
    opcoes = _resolver_opcoes(None)
    for tabela in tabelas:
        if tabela is not None:
            aplicar_estilo_tabela(tabela, opcoes)


def preencher_tabela(
    tabela: ttk.Treeview,
    itens: list[CotacaoResumo],
    mensagem_vazio: str | None = None,
) -> None:
    """Preenche linhas com cotacao formatada em pt-BR."""
    label_vazio = getattr(tabela, "_label_vazio", None)
    card_pai = getattr(tabela, "_card_pai", None)

    for linha in tabela.get_children():
        tabela.delete(linha)

    if not itens:
        if label_vazio is not None:
            texto = mensagem_vazio or "Nenhum registro no momento."
            label_vazio.configure(text=texto)
            label_vazio.pack(fill="x", padx=12, pady=(0, 12))
        if card_pai is not None:
            card_pai.configure(fg_color=CORES["superficie"])
        return

    if label_vazio is not None:
        label_vazio.pack_forget()

    aplicar_estilo_tabela(tabela)

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
