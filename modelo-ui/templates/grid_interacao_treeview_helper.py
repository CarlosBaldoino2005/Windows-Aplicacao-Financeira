"""
Hover, clique com toggle e duplo clique para ttk.Treeview (modelo UI global).

Copie para src/View/grid_interacao_treeview_helper.py e passe as cores do tema
(tokens selecao / selecaoTexto de design-tokens.json).

Uso minimo:

    from tkinter import ttk
    from src.View.grid_interacao_treeview_helper import (
        aplicar_destaque_estilo_treeview,
        configurar_interacao_treeview,
        obter_iid_linha_evento_treeview,
    )

    estilo = ttk.Style()
    aplicar_destaque_estilo_treeview(estilo, COR_FUNDO, COR_TEXTO)
    configurar_interacao_treeview(
        tabela,
        cor_fundo_destaque=COR_FUNDO,
        cor_texto_destaque=COR_TEXTO,
        ao_duplo_clique=minha_acao,
    )
"""
from __future__ import annotations

from collections.abc import Callable

import tkinter as tk
from tkinter import ttk

_TAG_HOVER = "hover"
_TAG_SELECIONADO = "selecionado"
_DELAY_TOGGLE_CLIQUE_MS = 280


def treeview_ainda_ativa(tabela: ttk.Treeview | None) -> bool:
    """Evita TclError quando a grid ja foi destruida (janela fechada)."""
    if tabela is None:
        return False
    try:
        return bool(tabela.winfo_exists())
    except (tk.TclError, RuntimeError, AttributeError):
        return False


def obter_iid_linha_evento_treeview(tabela: ttk.Treeview, evento) -> str | None:
    """Retorna o iid da linha clicada (independente da selecao atual)."""
    if not treeview_ainda_ativa(tabela):
        return None
    try:
        regiao = tabela.identify_region(evento.x, evento.y)
        if regiao not in ("cell", "tree"):
            return None
        iid = tabela.identify_row(evento.y)
        return iid if iid else None
    except tk.TclError:
        return None


def obter_iid_duplo_clique_treeview(tabela: ttk.Treeview, evento) -> str | None:
    """Iid da linha do duplo clique; usa coordenadas do mouse, nao a selecao."""
    iid = obter_iid_linha_evento_treeview(tabela, evento)
    if iid:
        return iid
    try:
        selecao = tabela.selection()
        return selecao[0] if selecao else None
    except tk.TclError:
        return None


def aplicar_destaque_tags_treeview(
    tabela: ttk.Treeview,
    cor_fundo_destaque: str,
    cor_texto_destaque: str,
) -> None:
    """Tags hover e selecionado com o mesmo azul (padrao global)."""
    tabela.tag_configure(_TAG_HOVER, background=cor_fundo_destaque, foreground=cor_texto_destaque)
    tabela.tag_configure(
        _TAG_SELECIONADO,
        background=cor_fundo_destaque,
        foreground=cor_texto_destaque,
    )


def aplicar_destaque_estilo_treeview(
    estilo: ttk.Style,
    cor_fundo_destaque: str,
    cor_texto_destaque: str,
) -> None:
    """Alinha a selecao nativa do ttk ao mesmo azul do hover."""
    estilo.map(
        "Treeview",
        background=[("selected", cor_fundo_destaque), ("selected", "!focus", cor_fundo_destaque)],
        foreground=[("selected", cor_texto_destaque), ("selected", "!focus", cor_texto_destaque)],
    )


def sincronizar_tags_selecao_treeview(tabela: ttk.Treeview) -> None:
    """Aplica tag azul nas linhas selecionadas e zebrado nas demais."""
    if not treeview_ainda_ativa(tabela):
        return
    try:
        selecionados = set(tabela.selection())
        tags_zebra = getattr(tabela, "_tags_zebra", {})
        for iid in tabela.get_children(""):
            if iid in selecionados:
                tabela.item(iid, tags=(_TAG_SELECIONADO,))
            else:
                tabela.item(iid, tags=(tags_zebra.get(iid, "par"),))
        limpar_hover_treeview(tabela)
    except tk.TclError:
        pass


def limpar_hover_treeview(tabela: ttk.Treeview) -> None:
    iid = getattr(tabela, "_linha_hover", None)
    if not iid:
        return
    try:
        if iid in tabela.get_children(""):
            restaurar_tag_linha_treeview(tabela, iid)
    except tk.TclError:
        pass
    tabela._linha_hover = None  # type: ignore[attr-defined]


def restaurar_tag_linha_treeview(tabela: ttk.Treeview, iid: str) -> None:
    if not treeview_ainda_ativa(tabela):
        return
    try:
        if iid in tabela.selection():
            tabela.item(iid, tags=(_TAG_SELECIONADO,))
            return
        tags_zebra = getattr(tabela, "_tags_zebra", {})
        tabela.item(iid, tags=(tags_zebra.get(iid, "par"),))
    except tk.TclError:
        pass


def _cancelar_toggle_clique_pendente(tabela: ttk.Treeview) -> None:
    job = getattr(tabela, "_toggle_clique_agendado", None)
    if job:
        try:
            tabela.after_cancel(job)
        except (tk.TclError, ValueError):
            pass
    tabela._toggle_clique_agendado = None  # type: ignore[attr-defined]
    tabela._toggle_clique_iid = None  # type: ignore[attr-defined]


def _executar_toggle_clique_pendente(tabela: ttk.Treeview, iid: str) -> None:
    tabela._toggle_clique_agendado = None  # type: ignore[attr-defined]
    tabela._toggle_clique_iid = None  # type: ignore[attr-defined]
    if not treeview_ainda_ativa(tabela) or not iid:
        return
    try:
        selecionados = set(tabela.selection())
        if iid in selecionados:
            selecionados.remove(iid)
        else:
            selecionados.add(iid)
        if selecionados:
            tabela.selection_set(tuple(selecionados))
        else:
            tabela.selection_set()
        sincronizar_tags_selecao_treeview(tabela)
    except tk.TclError:
        pass


def configurar_hover_treeview(tabela: ttk.Treeview) -> None:
    """Destaque azul na linha sob o cursor."""
    if getattr(tabela, "_hover_configurado", False):
        return
    tabela._hover_configurado = True  # type: ignore[attr-defined]
    tabela._linha_hover = None  # type: ignore[attr-defined]
    if not hasattr(tabela, "_tags_zebra"):
        tabela._tags_zebra = {}  # type: ignore[attr-defined]

    def ao_mover_mouse(evento) -> None:
        if not treeview_ainda_ativa(tabela):
            return
        try:
            iid = tabela.identify_row(evento.y)
            if iid == getattr(tabela, "_linha_hover", None):
                return
            limpar_hover_treeview(tabela)
            if iid and iid not in tabela.selection():
                tabela._linha_hover = iid  # type: ignore[attr-defined]
                tabela.item(iid, tags=(_TAG_HOVER,))
        except tk.TclError:
            pass

    def ao_sair_mouse(_evento=None) -> None:
        if not treeview_ainda_ativa(tabela):
            return
        limpar_hover_treeview(tabela)

    def ao_mudar_selecao(_evento=None) -> None:
        if not treeview_ainda_ativa(tabela):
            return
        sincronizar_tags_selecao_treeview(tabela)

    tabela.bind("<Motion>", ao_mover_mouse, add="+")
    tabela.bind("<Leave>", ao_sair_mouse, add="+")
    tabela.bind("<<TreeviewSelect>>", ao_mudar_selecao, add="+")


def configurar_selecao_clique_treeview(
    tabela: ttk.Treeview,
    delay_toggle_ms: int = _DELAY_TOGGLE_CLIQUE_MS,
) -> None:
    """
    Clique alterna selecao da linha (azul ligado/desligado).
    Permite varias linhas selecionadas (selectmode extended).
    """
    if getattr(tabela, "_selecao_clique_configurada", False):
        return
    tabela._selecao_clique_configurada = True  # type: ignore[attr-defined]
    tabela.configure(selectmode="extended")

    def ao_clicar_linha(evento) -> str | None:
        if not treeview_ainda_ativa(tabela):
            return "break"
        try:
            if tabela.identify_region(evento.x, evento.y) != "cell":
                return None
            iid = tabela.identify_row(evento.y)
            if not iid:
                return "break"

            _cancelar_toggle_clique_pendente(tabela)
            tabela._toggle_clique_iid = iid  # type: ignore[attr-defined]
            tabela._toggle_clique_agendado = tabela.after(  # type: ignore[attr-defined]
                delay_toggle_ms,
                lambda linha=iid: _executar_toggle_clique_pendente(tabela, linha),
            )
        except tk.TclError:
            pass
        return "break"

    tabela.bind("<Button-1>", ao_clicar_linha)


def configurar_duplo_clique_treeview(
    tabela: ttk.Treeview,
    ao_duplo_clique: Callable,
) -> None:
    """Duplo clique na linha sob o cursor; cancela toggle pendente do clique simples."""

    def ao_duplo_seguro(evento) -> None:
        if not treeview_ainda_ativa(tabela):
            return
        _cancelar_toggle_clique_pendente(tabela)
        iid = obter_iid_linha_evento_treeview(tabela, evento)
        if not iid:
            return
        try:
            tabela.selection_set(iid)
            sincronizar_tags_selecao_treeview(tabela)
        except tk.TclError:
            return
        ao_duplo_clique(evento)

    tabela.bind("<Double-1>", ao_duplo_seguro)


def configurar_interacao_treeview(
    tabela: ttk.Treeview,
    *,
    cor_fundo_destaque: str,
    cor_texto_destaque: str,
    ao_duplo_clique: Callable | None = None,
    delay_toggle_clique_ms: int = _DELAY_TOGGLE_CLIQUE_MS,
) -> None:
    """
    Aplica hover, clique com toggle e duplo clique (padrao global de grid).

    Chame aplicar_destaque_tags_treeview ao estilizar a grid (zebra + tags).
    Chame aplicar_destaque_estilo_treeview no ttk.Style da aplicacao.
    """
    aplicar_destaque_tags_treeview(tabela, cor_fundo_destaque, cor_texto_destaque)
    configurar_hover_treeview(tabela)
    configurar_selecao_clique_treeview(tabela, delay_toggle_ms=delay_toggle_clique_ms)
    if ao_duplo_clique is not None:
        configurar_duplo_clique_treeview(tabela, ao_duplo_clique)
