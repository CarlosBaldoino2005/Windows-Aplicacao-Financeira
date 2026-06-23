"""Grid da composicao da carteira de ETFs (padrao global Treeview)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from src.Model.composicao_etf import AtivoComposicaoEtf
from src.Model.opcoes_fonte_grid import OpcoesFonteGrid
from src.Tool.config_painel import ConfigPainelIni
from src.View.formatadores import formatar_percentual
from src.View.grid_ordenacao_helper import chave_comparavel
from src.View.grid_filtro_coluna_treeview_helper import (
    abrir_popup_filtro_coluna_treeview,
    aplicar_filtros_coluna_treeview,
    atualizar_cabecalhos_com_filtro_treeview,
    inicializar_filtros_coluna_treeview,
)
from src.View.grid_interacao_treeview_helper import (
    aplicar_destaque_estilo_treeview,
    aplicar_destaque_tags_treeview,
    configurar_interacao_treeview,
    liberar_interacao_treeview,
    sincronizar_tags_selecao_treeview,
    treeview_ainda_ativa,
)
from src.View.exportar_xlsx_grid_helper import (
    criar_frame_botoes_titulo_grid,
    vincular_botao_exportar_treeview,
)
from src.View.tema import CORES

_COLUNAS = ("ativo", "nome", "percentual")
_ROTULOS = {
    "ativo": "Ativo",
    "nome": "Nome",
    "percentual": "% da carteira",
}
_LARGURAS = (100, 520, 120)
_ANCORAS = {
    "ativo": "w",
    "nome": "w",
    "percentual": "e",
}
_FONTE_FAMILIA = "Segoe UI"


def _resolver_opcoes(opcoes: OpcoesFonteGrid | None) -> OpcoesFonteGrid:
    if opcoes is not None:
        return opcoes
    return ConfigPainelIni().carregar_opcoes_fonte_grid()


def _valor_celula_composicao_etf(ativo: AtivoComposicaoEtf, coluna: str) -> str:
    if coluna == "ativo":
        return ativo.simbolo
    if coluna == "nome":
        return ativo.nome
    if coluna == "percentual":
        return formatar_percentual(ativo.percentual / 100.0)
    return ""


def _atualizar_cabecalhos_ordenacao(tabela: ttk.Treeview) -> None:
    atualizar_cabecalhos_com_filtro_treeview(
        tabela,
        _COLUNAS,
        _ROTULOS,
        lambda coluna: _abrir_filtro_coluna_composicao_etf(tabela, coluna),
    )


def _abrir_filtro_coluna_composicao_etf(tabela: ttk.Treeview, coluna: str) -> None:
    abrir_popup_filtro_coluna_treeview(
        tabela=tabela,
        coluna=coluna,
        rotulo_coluna=_ROTULOS.get(coluna, coluna),
        linhas=list(getattr(tabela, "_itens_originais", [])),
        obter_valor=_valor_celula_composicao_etf,
        ao_atualizar=lambda: _renderizar_grid_composicao_etf(tabela),
        definir_ordenacao=lambda col, desc: _definir_ordenacao_composicao_etf(tabela, col, desc),
    )


def _definir_ordenacao_composicao_etf(tabela: ttk.Treeview, coluna: str, descendente: bool) -> None:
    tabela._coluna_ordenacao = coluna  # type: ignore[attr-defined]
    tabela._ordenacao_desc = descendente  # type: ignore[attr-defined]


def _configurar_ordenacao_colunas(tabela: ttk.Treeview) -> None:
    if getattr(tabela, "_ordenacao_configurada", False):
        return
    tabela._ordenacao_configurada = True  # type: ignore[attr-defined]
    tabela._coluna_ordenacao = "percentual"  # type: ignore[attr-defined]
    tabela._ordenacao_desc = True  # type: ignore[attr-defined]
    tabela._itens_originais: list[AtivoComposicaoEtf] = []  # type: ignore[attr-defined]
    inicializar_filtros_coluna_treeview(tabela)
    _atualizar_cabecalhos_ordenacao(tabela)


def _chave_ordenacao(item: AtivoComposicaoEtf, coluna: str) -> tuple:
    if coluna == "ativo":
        return chave_comparavel(item.simbolo.upper())
    if coluna == "nome":
        return chave_comparavel(item.nome.upper())
    if coluna == "percentual":
        return chave_comparavel(item.percentual)
    return chave_comparavel("")


def _ordenar_ativos(
    ativos: list[AtivoComposicaoEtf],
    coluna: str | None,
    descendente: bool,
) -> list[AtivoComposicaoEtf]:
    if not coluna or not ativos:
        return ativos
    return sorted(
        ativos,
        key=lambda item: _chave_ordenacao(item, coluna),
        reverse=descendente,
    )


def criar_grid_composicao_etf(
    pai: ctk.CTkBaseClass,
    titulo: str,
    *,
    altura: int = 12,
    ao_duplo_clique: Callable | None = None,
) -> ttk.Treeview:
    """Cria card com grid zebrada, hover e ordenacao por coluna."""
    card = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=12)
    card.pack(fill="both", expand=True)

    linha_titulo = ctk.CTkFrame(card, fg_color="transparent")
    linha_titulo.pack(fill="x", padx=12, pady=(12, 4))

    ctk.CTkLabel(
        linha_titulo,
        text=titulo,
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=CORES["texto"],
    ).pack(side="left", anchor="w")

    frame_botoes = criar_frame_botoes_titulo_grid(linha_titulo)

    ctk.CTkLabel(
        card,
        text=(
            "Clique no titulo da coluna para filtrar e ordenar. "
            "Passe o mouse para destacar a linha; clique para selecionar."
        ),
        font=ctk.CTkFont(size=11),
        text_color=CORES["textoSecundario"],
    ).pack(anchor="w", padx=12, pady=(0, 8))

    frame_tabela = ctk.CTkFrame(card, fg_color="transparent")
    frame_tabela.pack(fill="both", expand=True, padx=12, pady=(0, 8))

    tabela = ttk.Treeview(
        frame_tabela,
        columns=_COLUNAS,
        show="headings",
        height=altura,
        selectmode="extended",
    )
    scroll = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela.yview)
    tabela.configure(yscrollcommand=scroll.set)
    tabela.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    _configurar_ordenacao_colunas(tabela)

    for coluna in _COLUNAS:
        largura = _LARGURAS[_COLUNAS.index(coluna)]
        tabela.column(
            coluna,
            width=largura,
            minwidth=80 if coluna != "nome" else 200,
            stretch=coluna == "nome",
            anchor=_ANCORAS[coluna],
        )

    aplicar_estilo_grid_composicao_etf(tabela)
    configurar_interacao_treeview(tabela, ao_duplo_clique=ao_duplo_clique)

    label_vazio = ctk.CTkLabel(
        card,
        text="Nenhum ativo retornado para este ETF.",
        font=ctk.CTkFont(size=13),
        text_color=CORES["textoSecundario"],
    )
    label_vazio.pack(pady=(0, 12))
    label_vazio.pack_forget()

    tabela._card_pai = card  # type: ignore[attr-defined]
    tabela._label_vazio = label_vazio  # type: ignore[attr-defined]
    _atualizar_cabecalhos_ordenacao(tabela)
    vincular_botao_exportar_treeview(frame_botoes, tabela, titulo, janela_pai=card)
    return tabela


def aplicar_estilo_grid_composicao_etf(
    tabela: ttk.Treeview,
    opcoes_fonte: OpcoesFonteGrid | None = None,
) -> None:
    if not treeview_ainda_ativa(tabela):
        return

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
    aplicar_destaque_estilo_treeview(estilo)

    tabela.tag_configure("normal_par", background=CORES["zebraClara"], foreground=CORES["texto"])
    tabela.tag_configure("normal_impar", background=CORES["zebraEscura"], foreground=CORES["texto"])
    aplicar_destaque_tags_treeview(tabela)


def preencher_grid_composicao_etf(
    tabela: ttk.Treeview,
    ativos: list[AtivoComposicaoEtf],
) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    _configurar_ordenacao_colunas(tabela)
    tabela._itens_originais = list(ativos)  # type: ignore[attr-defined]
    _renderizar_grid_composicao_etf(tabela)


def _renderizar_grid_composicao_etf(tabela: ttk.Treeview) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    ativos_originais = list(getattr(tabela, "_itens_originais", []))
    ativos = aplicar_filtros_coluna_treeview(ativos_originais, tabela, _valor_celula_composicao_etf)
    coluna_ord = getattr(tabela, "_coluna_ordenacao", None)
    descendente = getattr(tabela, "_ordenacao_desc", False)
    ativos_exibir = _ordenar_ativos(ativos, coluna_ord, descendente)
    _atualizar_cabecalhos_ordenacao(tabela)

    label_vazio = getattr(tabela, "_label_vazio", None)
    selecionados_antes = set(tabela.selection())
    liberar_interacao_treeview(tabela)
    tabela._tags_zebra = {}  # type: ignore[attr-defined]

    try:
        for item_id in tabela.get_children():
            tabela.delete(item_id)
    except tk.TclError:
        return

    if not ativos_exibir:
        if label_vazio is not None:
            if ativos_originais:
                label_vazio.configure(text="Nenhum ativo corresponde aos filtros atuais.")
            else:
                label_vazio.configure(text="Nenhum ativo retornado para este ETF.")
            label_vazio.pack(pady=(0, 12))
        tabela.selection_set()
        return

    if label_vazio is not None:
        label_vazio.pack_forget()

    aplicar_estilo_grid_composicao_etf(tabela)

    for indice, ativo in enumerate(ativos_exibir):
        iid = f"{ativo.simbolo}_{indice}"
        tag = "normal_par" if indice % 2 == 0 else "normal_impar"
        tabela._tags_zebra[iid] = tag  # type: ignore[attr-defined]
        tabela.insert(
            "",
            "end",
            iid=iid,
            values=(
                ativo.simbolo,
                ativo.nome,
                formatar_percentual(ativo.percentual / 100.0),
            ),
            tags=(tag,),
        )

    iids_visiveis = {f"{ativo.simbolo}_{i}" for i, ativo in enumerate(ativos_exibir)}
    selecionados_depois = tuple(selecionados_antes & iids_visiveis)
    if selecionados_depois:
        tabela.selection_set(selecionados_depois)
    else:
        tabela.selection_set()

    sincronizar_tags_selecao_treeview(tabela)


def liberar_grid_composicao_etf(tabela: ttk.Treeview | None) -> None:
    liberar_interacao_treeview(tabela)
