"""Hover, clique com toggle e duplo clique para ttk.Treeview (padrao global de grid)."""
from __future__ import annotations

from collections.abc import Callable

import tkinter as tk
from tkinter import ttk

from src.View.tema import CORES

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


def obter_simbolo_duplo_clique_treeview(tabela: ttk.Treeview, evento) -> str | None:
    """Simbolo/iid da linha do duplo clique; usa coordenadas do mouse, nao a selecao."""
    iid = obter_iid_linha_evento_treeview(tabela, evento)
    if iid:
        return iid
    try:
        selecao = tabela.selection()
        return selecao[0] if selecao else None
    except tk.TclError:
        return None


def obter_simbolo_unico_selecionado_treeview(tabela: ttk.Treeview | None) -> str | None:
    """Retorna o simbolo/iid quando ha exatamente uma linha selecionada na grid."""
    if not treeview_ainda_ativa(tabela):
        return None
    try:
        selecionados = tabela.selection()
        if len(selecionados) == 1:
            return selecionados[0]
    except tk.TclError:
        return None
    return None


def _cores_destaque_linha_treeview() -> tuple[str, str]:
    """Mesmo azul para hover e para linha selecionada com clique."""
    return CORES["selecao"], CORES["selecaoTexto"]


def aplicar_destaque_tags_treeview(tabela: ttk.Treeview) -> None:
    fundo, texto = _cores_destaque_linha_treeview()
    tabela.tag_configure(_TAG_HOVER, background=fundo, foreground=texto)
    tabela.tag_configure(_TAG_SELECIONADO, background=fundo, foreground=texto)


def aplicar_destaque_estilo_treeview(estilo: ttk.Style) -> None:
    """Alinha a selecao nativa do ttk ao mesmo azul do hover."""
    fundo, texto = _cores_destaque_linha_treeview()
    estilo.map(
        "Treeview",
        background=[("selected", fundo), ("selected", "!focus", fundo)],
        foreground=[("selected", texto), ("selected", "!focus", texto)],
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
        alvo = getattr(tabela, "_toggle_after_alvo", None)
        if alvo is None:
            try:
                alvo = tabela.winfo_toplevel()
            except tk.TclError:
                alvo = None
        if alvo is not None:
            try:
                if alvo.winfo_exists():
                    alvo.after_cancel(job)
            except (tk.TclError, ValueError, RuntimeError):
                pass
    tabela._toggle_clique_agendado = None  # type: ignore[attr-defined]
    tabela._toggle_clique_iid = None  # type: ignore[attr-defined]
    tabela._toggle_after_alvo = None  # type: ignore[attr-defined]


def liberar_interacao_treeview(tabela: ttk.Treeview | None) -> None:
    """Cancela timers pendentes ao fechar janela ou recarregar a grid."""
    if tabela is None:
        return
    _cancelar_toggle_clique_pendente(tabela)
    if treeview_ainda_ativa(tabela):
        limpar_hover_treeview(tabela)


def _executar_toggle_clique_pendente(tabela: ttk.Treeview, iid: str) -> None:
    tabela._toggle_clique_agendado = None  # type: ignore[attr-defined]
    tabela._toggle_clique_iid = None  # type: ignore[attr-defined]
    tabela._toggle_after_alvo = None  # type: ignore[attr-defined]
    if not treeview_ainda_ativa(tabela) or not iid:
        return
    try:
        if not tabela.exists(iid):
            return
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
    """Destaque azul na linha sob o cursor (padrao global de grid)."""
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

    tabela.bind("<Motion>", ao_mover_mouse, add=True)
    tabela.bind("<Leave>", ao_sair_mouse, add=True)
    tabela.bind("<<TreeviewSelect>>", ao_mudar_selecao, add=True)


def configurar_selecao_clique_treeview(tabela: ttk.Treeview) -> None:
    """
    Clique alterna selecao da linha (azul ligado/desligado).
    Permite varias linhas selecionadas ao mesmo tempo.
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
            alvo = tabela.winfo_toplevel()
            tabela._toggle_clique_iid = iid  # type: ignore[attr-defined]
            tabela._toggle_after_alvo = alvo  # type: ignore[attr-defined]
            tabela._toggle_clique_agendado = alvo.after(  # type: ignore[attr-defined]
                _DELAY_TOGGLE_CLIQUE_MS,
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
    """Duplo clique usa a linha sob o cursor; cancela toggle pendente do clique simples."""

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
    ao_duplo_clique: Callable | None = None,
) -> None:
    """Aplica hover, clique com toggle e duplo clique (padrao global de grid)."""
    aplicar_destaque_tags_treeview(tabela)
    configurar_hover_treeview(tabela)
    configurar_selecao_clique_treeview(tabela)
    if ao_duplo_clique is not None:
        configurar_duplo_clique_treeview(tabela, ao_duplo_clique)

    def ao_destruir_grid(_evento=None) -> None:
        _cancelar_toggle_clique_pendente(tabela)

    tabela.bind("<Destroy>", ao_destruir_grid, add=True)


if __name__ == "__main__":
    print(
        "Helper de interacao de grid — importe em telas com Treeview.\n"
        "Para abrir o app Financeiro, use executar.bat na raiz do projeto."
    )
