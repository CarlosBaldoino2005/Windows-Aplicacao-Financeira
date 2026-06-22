"""Grid da fita de negocios do Agora (padrao global Treeview)."""
from __future__ import annotations

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from src.Model.negocio_agora import NegocioAgora
from src.Model.opcoes_fonte_grid import OpcoesFonteGrid
from src.Tool.config_painel import ConfigPainelIni
from src.View.formatadores import formatar_inteiro_ptbr, formatar_preco_negocio
from src.View.grid_ordenacao_helper import SUFIXO_ASCENDENTE, SUFIXO_DESCENDENTE, chave_comparavel
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

_COLUNAS = (
    "hora",
    "preco",
    "tamanho",
    "tipo",
    "bs",
    "compra",
    "venda",
    "total_volume",
    "num",
    "bolsa",
)
_ROTULOS = {
    "hora": "Hora",
    "preco": "Preco",
    "tamanho": "Tamanho",
    "tipo": "Tipo",
    "bs": "B/S",
    "compra": "Compra",
    "venda": "Venda",
    "total_volume": "Total Volume",
    "num": "Num",
    "bolsa": "Bolsa",
}
_LARGURAS = (88, 88, 88, 56, 88, 88, 88, 100, 72, 64)
_ANCORAS = {
    "hora": "center",
    "preco": "e",
    "tamanho": "e",
    "tipo": "center",
    "bs": "center",
    "compra": "e",
    "venda": "e",
    "total_volume": "e",
    "num": "e",
    "bolsa": "center",
}
_FONTE_FAMILIA = "Segoe UI"
_TAGS_LADO = {
    "compra": "lado_compra",
    "venda": "lado_venda",
    "neutro": "lado_neutro",
}


def _resolver_opcoes(opcoes: OpcoesFonteGrid | None) -> OpcoesFonteGrid:
    if opcoes is not None:
        return opcoes
    return ConfigPainelIni().carregar_opcoes_fonte_grid()


def _rotulo_lado(lado: str) -> str:
    if lado == "compra":
        return "Compra"
    if lado == "venda":
        return "Venda"
    return "Neutro"


def _atualizar_cabecalhos_ordenacao(tabela: ttk.Treeview) -> None:
    coluna_ativa = getattr(tabela, "_coluna_ordenacao", None)
    descendente = getattr(tabela, "_ordenacao_desc", False)
    for coluna in _COLUNAS:
        texto = _ROTULOS[coluna]
        if coluna_ativa == coluna:
            texto += SUFIXO_DESCENDENTE if descendente else SUFIXO_ASCENDENTE
        tabela.heading(
            coluna,
            text=texto,
            command=lambda c=coluna: alternar_ordenacao_negocios_agora(tabela, c),
        )


def _configurar_ordenacao_colunas(tabela: ttk.Treeview) -> None:
    if getattr(tabela, "_ordenacao_configurada", False):
        return
    tabela._ordenacao_configurada = True  # type: ignore[attr-defined]
    tabela._coluna_ordenacao = "hora"  # type: ignore[attr-defined]
    tabela._ordenacao_desc = True  # type: ignore[attr-defined]
    tabela._itens_originais: list[NegocioAgora] = []  # type: ignore[attr-defined]

    for coluna in _COLUNAS:
        tabela.heading(
            coluna,
            text=_ROTULOS[coluna],
            command=lambda c=coluna: alternar_ordenacao_negocios_agora(tabela, c),
        )


def alternar_ordenacao_negocios_agora(tabela: ttk.Treeview, coluna: str) -> None:
    if getattr(tabela, "_coluna_ordenacao", None) == coluna:
        tabela._ordenacao_desc = not getattr(tabela, "_ordenacao_desc", False)  # type: ignore[attr-defined]
    else:
        tabela._coluna_ordenacao = coluna  # type: ignore[attr-defined]
        tabela._ordenacao_desc = coluna in ("hora", "num")  # type: ignore[attr-defined]

    itens = list(getattr(tabela, "_itens_originais", []))
    preencher_grid_negocios_agora(tabela, itens)


def _chave_ordenacao(item: NegocioAgora, coluna: str) -> tuple:
    if coluna == "hora":
        return chave_comparavel(item.hora)
    if coluna == "preco":
        return chave_comparavel(item.preco)
    if coluna == "tamanho":
        return chave_comparavel(item.tamanho)
    if coluna == "tipo":
        return chave_comparavel(item.tipo.upper())
    if coluna == "bs":
        return chave_comparavel(_rotulo_lado(item.lado))
    if coluna == "compra":
        return chave_comparavel(item.preco_compra)
    if coluna == "venda":
        return chave_comparavel(item.preco_venda)
    if coluna == "total_volume":
        return chave_comparavel(item.total_volume)
    if coluna == "num":
        return chave_comparavel(item.numero)
    if coluna == "bolsa":
        return chave_comparavel(item.bolsa.upper())
    return chave_comparavel("")


def _ordenar_negocios(
    negocios: list[NegocioAgora],
    coluna: str | None,
    descendente: bool,
) -> list[NegocioAgora]:
    if not coluna or not negocios:
        return negocios
    return sorted(
        negocios,
        key=lambda item: _chave_ordenacao(item, coluna),
        reverse=descendente,
    )


def _tag_linha(item: NegocioAgora, indice: int) -> str:
    zebra = "par" if indice % 2 == 0 else "impar"
    lado = _TAGS_LADO.get(item.lado, "lado_neutro")
    return f"{zebra}_{lado}"


def criar_grid_negocios_agora(
    pai: ctk.CTkBaseClass,
    titulo: str,
    *,
    altura: int = 22,
) -> ttk.Treeview:
    """Cria card com grid zebrada, cores por lado e ordenacao por coluna."""
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
            "Negocios do dia (mais recentes no topo). "
            "Colunas no padrao ADVFN; dados intraday agregados por minuto."
        ),
        font=ctk.CTkFont(size=11),
        text_color=CORES["textoSecundario"],
    ).pack(anchor="w", padx=12, pady=(0, 8))

    frame_tabela = ctk.CTkFrame(card, fg_color="transparent")
    frame_tabela.pack(fill="both", expand=True, padx=12, pady=(0, 8))
    frame_tabela.grid_columnconfigure(0, weight=1)
    frame_tabela.grid_rowconfigure(0, weight=1)

    tabela = ttk.Treeview(
        frame_tabela,
        columns=_COLUNAS,
        show="headings",
        height=altura,
        selectmode="extended",
    )
    scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela.yview)
    scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=tabela.xview)
    tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    tabela.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")

    _configurar_ordenacao_colunas(tabela)

    for coluna in _COLUNAS:
        largura = _LARGURAS[_COLUNAS.index(coluna)]
        tabela.column(
            coluna,
            width=largura,
            minwidth=56,
            stretch=False,
            anchor=_ANCORAS[coluna],
        )

    aplicar_estilo_grid_negocios_agora(tabela)
    configurar_interacao_treeview(tabela)

    label_vazio = ctk.CTkLabel(
        card,
        text="Nenhum negocio registrado para o dia.",
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


def aplicar_estilo_grid_negocios_agora(
    tabela: ttk.Treeview,
    opcoes_fonte: OpcoesFonteGrid | None = None,
) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    opcoes = _resolver_opcoes(opcoes_fonte)
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure(
        "NegociosAgora.Treeview",
        background=CORES["zebraClara"],
        fieldbackground=CORES["zebraClara"],
        foreground=CORES["texto"],
        borderwidth=0,
        rowheight=opcoes.altura_linha,
        font=(_FONTE_FAMILIA, opcoes.fonte_tree),
    )
    estilo.configure(
        "NegociosAgora.Treeview.Heading",
        background=CORES["zebraEscura"],
        foreground=CORES["texto"],
        font=(_FONTE_FAMILIA, opcoes.fonte_cabecalho_tree, "bold"),
        relief="flat",
    )
    estilo.layout("NegociosAgora.Treeview", estilo.layout("Treeview"))
    tabela.configure(style="NegociosAgora.Treeview")
    aplicar_destaque_estilo_treeview(estilo)

    for zebra, fundo in (("par", CORES["zebraClara"]), ("impar", CORES["zebraEscura"])):
        tabela.tag_configure(f"{zebra}_lado_compra", background=fundo, foreground=CORES["sucesso"])
        tabela.tag_configure(f"{zebra}_lado_venda", background=fundo, foreground=CORES["erro"])
        tabela.tag_configure(f"{zebra}_lado_neutro", background=fundo, foreground=CORES["textoSecundario"])

    aplicar_destaque_tags_treeview(tabela)


def preencher_grid_negocios_agora(
    tabela: ttk.Treeview,
    negocios: list[NegocioAgora],
) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    tabela._itens_originais = list(negocios)  # type: ignore[attr-defined]
    coluna = getattr(tabela, "_coluna_ordenacao", "hora")
    descendente = getattr(tabela, "_ordenacao_desc", True)
    ordenados = _ordenar_negocios(negocios, coluna, descendente)

    selecionados = set(tabela.selection())
    filhos = tabela.get_children()
    if filhos:
        tabela.delete(*filhos)

    for indice, item in enumerate(ordenados):
        valores = (
            item.hora,
            formatar_preco_negocio(item.preco),
            formatar_inteiro_ptbr(item.tamanho),
            item.tipo or "",
            _rotulo_lado(item.lado),
            formatar_preco_negocio(item.preco_compra),
            formatar_preco_negocio(item.preco_venda),
            formatar_inteiro_ptbr(item.total_volume),
            formatar_inteiro_ptbr(item.numero),
            item.bolsa,
        )
        tabela.insert(
            "",
            "end",
            iid=item.id,
            values=valores,
            tags=(_tag_linha(item, indice),),
        )

    label_vazio = getattr(tabela, "_label_vazio", None)
    if label_vazio is not None:
        if ordenados:
            label_vazio.pack_forget()
        else:
            label_vazio.pack(pady=(0, 12))

    if selecionados:
        existentes = [iid for iid in selecionados if tabela.exists(iid)]
        if existentes:
            tabela.selection_set(existentes)

    sincronizar_tags_selecao_treeview(tabela)
    _atualizar_cabecalhos_ordenacao(tabela)


def liberar_grid_negocios_agora(tabela: ttk.Treeview | None) -> None:
    liberar_interacao_treeview(tabela)
