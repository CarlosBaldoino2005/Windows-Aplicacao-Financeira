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
from src.View.grid_ordenacao_helper import SUFIXO_ASCENDENTE, SUFIXO_DESCENDENTE
from src.View.grid_interacao_treeview_helper import (
    aplicar_destaque_estilo_treeview,
    aplicar_destaque_tags_treeview,
    configurar_interacao_treeview,
    limpar_hover_treeview,
    obter_simbolo_duplo_clique_treeview,
    sincronizar_tags_selecao_treeview,
    treeview_ainda_ativa,
)
from src.View.tema import CORES

_COLUNAS_PADRAO = ("simbolo", "nome", "preco", "variacao")
_ROTULOS_COLUNA_BASE = {
    "simbolo": "Acao",
    "nome": "Nome",
    "preco": "Preco",
    "variacao": "Variacao",
}
_FONTE_FAMILIA = "Segoe UI"


def _resolver_opcoes(opcoes: OpcoesFonteGrid | None) -> OpcoesFonteGrid:
    if opcoes is not None:
        return opcoes
    return ConfigPainelIni().carregar_opcoes_fonte_grid()


def definir_rotulo_coluna_variacao(tabela: ttk.Treeview, rotulo: str) -> None:
    """Altera o cabecalho da coluna de variacao (ex.: periodo selecionado)."""
    tabela._rotulo_variacao = rotulo  # type: ignore[attr-defined]
    _atualizar_cabecalhos_ordenacao(tabela)


def definir_rotulo_coluna_simbolo(tabela: ttk.Treeview, rotulo: str) -> None:
    """Altera o cabecalho da coluna de ticker (ex.: FII em fundos imobiliarios)."""
    tabela._rotulo_simbolo = rotulo  # type: ignore[attr-defined]
    _atualizar_cabecalhos_ordenacao(tabela)


def _rotulo_base_coluna(tabela: ttk.Treeview, coluna: str) -> str:
    if coluna == "variacao":
        return getattr(tabela, "_rotulo_variacao", _ROTULOS_COLUNA_BASE["variacao"])
    if coluna == "simbolo":
        return getattr(tabela, "_rotulo_simbolo", _ROTULOS_COLUNA_BASE["simbolo"])
    return _ROTULOS_COLUNA_BASE[coluna]


def _atualizar_cabecalhos_ordenacao(tabela: ttk.Treeview) -> None:
    coluna_ativa = getattr(tabela, "_coluna_ordenacao", None)
    descendente = getattr(tabela, "_ordenacao_desc", False)
    for coluna in _COLUNAS_PADRAO:
        texto = _rotulo_base_coluna(tabela, coluna)
        if coluna_ativa == coluna:
            texto += SUFIXO_DESCENDENTE if descendente else SUFIXO_ASCENDENTE
        tabela.heading(
            coluna,
            text=texto,
            command=lambda c=coluna: _alternar_ordenacao_tabela(tabela, c),
        )


def _configurar_ordenacao_colunas(tabela: ttk.Treeview) -> None:
    if getattr(tabela, "_ordenacao_configurada", False):
        return
    tabela._ordenacao_configurada = True  # type: ignore[attr-defined]
    tabela._coluna_ordenacao = None  # type: ignore[attr-defined]
    tabela._ordenacao_desc = False  # type: ignore[attr-defined]
    tabela._rotulo_variacao = _ROTULOS_COLUNA_BASE["variacao"]  # type: ignore[attr-defined]
    tabela._itens_originais: list[CotacaoResumo] = []  # type: ignore[attr-defined]

    for coluna in _COLUNAS_PADRAO:
        tabela.heading(
            coluna,
            text=_ROTULOS_COLUNA_BASE[coluna],
            command=lambda c=coluna: _alternar_ordenacao_tabela(tabela, c),
        )


def _alternar_ordenacao_tabela(tabela: ttk.Treeview, coluna: str) -> None:
    if getattr(tabela, "_coluna_ordenacao", None) == coluna:
        tabela._ordenacao_desc = not getattr(tabela, "_ordenacao_desc", False)  # type: ignore[attr-defined]
    else:
        tabela._coluna_ordenacao = coluna  # type: ignore[attr-defined]
        tabela._ordenacao_desc = False  # type: ignore[attr-defined]

    itens = list(getattr(tabela, "_itens_originais", []))
    mensagem_vazio = getattr(tabela, "_mensagem_vazio_atual", None)
    preencher_tabela(tabela, itens, mensagem_vazio)


def _ordenar_cotacoes(
    itens: list[CotacaoResumo],
    coluna: str | None,
    descendente: bool,
) -> list[CotacaoResumo]:
    if not coluna or not itens:
        return itens

    def chave(item: CotacaoResumo):
        if coluna == "simbolo":
            return item.simbolo.lower()
        if coluna == "nome":
            return item.nome.lower()
        if coluna == "preco":
            return item.preco
        if coluna == "variacao":
            return item.variacao_percentual
        return ""

    return sorted(itens, key=chave, reverse=descendente)


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
    _configurar_ordenacao_colunas(tabela)

    tabela.pack(fill="both", expand=expandir)
    aplicar_estilo_tabela(tabela, opcoes)
    configurar_interacao_treeview(tabela, ao_duplo_clique=ao_duplo_clique)

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
    tabela.tag_configure("par", background=CORES["zebraClara"])
    tabela.tag_configure("impar", background=CORES["zebraEscura"])
    aplicar_destaque_tags_treeview(tabela)

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
        if treeview_ainda_ativa(tabela):
            aplicar_estilo_tabela(tabela, opcoes)


def preencher_tabela(
    tabela: ttk.Treeview,
    itens: list[CotacaoResumo],
    mensagem_vazio: str | None = None,
) -> None:
    """Preenche linhas com cotacao formatada em pt-BR."""
    if not treeview_ainda_ativa(tabela):
        return
    try:
        _preencher_tabela_interno(tabela, itens, mensagem_vazio)
    except tk.TclError:
        pass


def _preencher_tabela_interno(
    tabela: ttk.Treeview,
    itens: list[CotacaoResumo],
    mensagem_vazio: str | None = None,
) -> None:
    _configurar_ordenacao_colunas(tabela)
    label_vazio = getattr(tabela, "_label_vazio", None)
    card_pai = getattr(tabela, "_card_pai", None)
    tabela._itens_originais = list(itens)  # type: ignore[attr-defined]
    tabela._mensagem_vazio_atual = mensagem_vazio  # type: ignore[attr-defined]

    coluna_ord = getattr(tabela, "_coluna_ordenacao", None)
    descendente = getattr(tabela, "_ordenacao_desc", False)
    itens_exibir = _ordenar_cotacoes(itens, coluna_ord, descendente)

    selecionados_antes = set(tabela.selection())
    limpar_hover_treeview(tabela)
    tabela._tags_zebra = {}  # type: ignore[attr-defined]

    for linha in tabela.get_children():
        tabela.delete(linha)

    if not itens_exibir:
        if label_vazio is not None:
            texto = mensagem_vazio or "Nenhum registro no momento."
            label_vazio.configure(text=texto)
            label_vazio.pack(fill="x", padx=12, pady=(0, 12))
        if card_pai is not None:
            card_pai.configure(fg_color=CORES["superficie"])
        tabela.selection_set()
        _atualizar_cabecalhos_ordenacao(tabela)
        return

    if label_vazio is not None:
        label_vazio.pack_forget()

    aplicar_estilo_tabela(tabela)

    for i, item in enumerate(itens_exibir):
        tag = "par" if i % 2 == 0 else "impar"
        tabela._tags_zebra[item.simbolo] = tag  # type: ignore[attr-defined]
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

    iids_visiveis = {item.simbolo for item in itens_exibir}
    selecionados_depois = tuple(selecionados_antes & iids_visiveis)
    if selecionados_depois:
        tabela.selection_set(selecionados_depois)
    else:
        tabela.selection_set()

    sincronizar_tags_selecao_treeview(tabela)
    _atualizar_cabecalhos_ordenacao(tabela)
