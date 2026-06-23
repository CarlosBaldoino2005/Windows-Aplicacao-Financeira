"""Filtro estilo Excel por coluna em ttk.Treeview (popup com busca e checkboxes)."""
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Iterable, Sequence
from tkinter import ttk
from typing import Any, TypeVar

import customtkinter as ctk

from src.View.grid_ordenacao_helper import SUFIXO_ASCENDENTE, SUFIXO_DESCENDENTE
from src.View.grid_interacao_treeview_helper import treeview_ainda_ativa
from src.View.tema import CORES

T = TypeVar("T")

SUFIXO_FILTRO_ATIVO = " \u25be"
_LARGURA_POPUP = 280
_ALTURA_LISTA = 220
_VALOR_VAZIO = "(Vazio)"
_ROTULO_SELECIONAR_TUDO = "(Selecionar Tudo)"

_popup_aberto: ctk.CTkToplevel | None = None


def inicializar_filtros_coluna_treeview(tabela: ttk.Treeview) -> None:
    """Prepara o dicionario de filtros ativos por coluna."""
    tabela._filtros_coluna = {}  # type: ignore[attr-defined]


def coluna_com_filtro_ativo(tabela: ttk.Treeview, coluna: str) -> bool:
    filtros: dict[str, set[str] | None] = getattr(tabela, "_filtros_coluna", {})
    selecionados = filtros.get(coluna)
    return selecionados is not None


def aplicar_filtros_coluna_treeview(
    linhas: list[T],
    tabela: ttk.Treeview,
    obter_valor: Callable[[T, str], str],
) -> list[T]:
    """Mantem apenas linhas cujos valores passam em todos os filtros ativos."""
    filtros: dict[str, set[str] | None] = getattr(tabela, "_filtros_coluna", {})
    if not filtros or not linhas:
        return linhas

    resultado: list[T] = []
    for linha in linhas:
        if _linha_passa_filtros(linha, filtros, obter_valor):
            resultado.append(linha)
    return resultado


def _resolver_rotulo_coluna(
    rotulos: dict[str, str] | Callable[[str], str],
    coluna: str,
) -> str:
    if callable(rotulos):
        return rotulos(coluna)
    return rotulos.get(coluna, coluna)


def atualizar_cabecalhos_com_filtro_treeview(
    tabela: ttk.Treeview,
    colunas: Sequence[str],
    rotulos: dict[str, str] | Callable[[str], str],
    ao_abrir_filtro: Callable[[str], None],
) -> None:
    """Atualiza titulos com setas de ordenacao e indicador de filtro ativo."""
    coluna_ordenacao = getattr(tabela, "_coluna_ordenacao", None)
    descendente = getattr(tabela, "_ordenacao_desc", False)

    for coluna in colunas:
        texto = formatar_titulo_cabecalho_coluna(
            _resolver_rotulo_coluna(rotulos, coluna),
            ordenado=coluna_ordenacao == coluna,
            descendente=descendente,
            filtro_ativo=coluna_com_filtro_ativo(tabela, coluna),
        )
        tabela.heading(
            coluna,
            text=texto,
            command=lambda c=coluna: ao_abrir_filtro(c),
        )


def formatar_titulo_cabecalho_coluna(
    rotulo: str,
    *,
    ordenado: bool,
    descendente: bool,
    filtro_ativo: bool,
) -> str:
    texto = rotulo
    if ordenado:
        texto += SUFIXO_DESCENDENTE if descendente else SUFIXO_ASCENDENTE
    if filtro_ativo:
        texto += SUFIXO_FILTRO_ATIVO
    return texto


def abrir_popup_filtro_coluna_treeview(
    *,
    tabela: ttk.Treeview,
    coluna: str,
    rotulo_coluna: str,
    linhas: list[T],
    obter_valor: Callable[[T, str], str],
    ao_atualizar: Callable[[], None],
    definir_ordenacao: Callable[[str, bool], None],
) -> None:
    """Abre menu de filtro/ordenacao abaixo do cabecalho da coluna."""
    global _popup_aberto

    if not treeview_ainda_ativa(tabela):
        return

    if _popup_aberto is not None:
        try:
            if _popup_aberto.winfo_exists():
                _popup_aberto.destroy()
        except tk.TclError:
            pass
        _popup_aberto = None

    filtros: dict[str, set[str] | None] = getattr(tabela, "_filtros_coluna", {})
    selecionados_atuais = filtros.get(coluna)
    valores_unicos = _valores_unicos_coluna(linhas, coluna, obter_valor)

    if selecionados_atuais is None:
        selecionados_iniciais = set(valores_unicos)
    else:
        selecionados_iniciais = set(selecionados_atuais)

    raiz = tabela.winfo_toplevel()
    popup = ctk.CTkToplevel(raiz)
    _popup_aberto = popup
    popup.title(f"Filtro — {rotulo_coluna}")
    popup.configure(fg_color=CORES["superficie"])
    popup.resizable(False, False)
    popup.transient(raiz)

    pos_x, pos_y = _calcular_posicao_popup(tabela, coluna)
    popup.geometry(f"{_LARGURA_POPUP}x460+{pos_x}+{pos_y}")
    popup.minsize(_LARGURA_POPUP, 460)

    def _fechar() -> None:
        global _popup_aberto
        try:
            popup.grab_release()
        except tk.TclError:
            pass
        try:
            popup.destroy()
        except tk.TclError:
            pass
        if _popup_aberto is popup:
            _popup_aberto = None

    popup.protocol("WM_DELETE_WINDOW", _fechar)

    conteudo = ctk.CTkFrame(popup, fg_color="transparent")
    conteudo.pack(fill="both", expand=True, padx=12, pady=12)

    ctk.CTkButton(
        conteudo,
        text="Classificar de A a Z",
        anchor="w",
        fg_color="transparent",
        hover_color=CORES["zebraEscura"],
        text_color=CORES["texto"],
        command=lambda: _ordenar_e_fechar(definir_ordenacao, coluna, False, ao_atualizar, _fechar),
    ).pack(fill="x", pady=(0, 4))

    ctk.CTkButton(
        conteudo,
        text="Classificar de Z a A",
        anchor="w",
        fg_color="transparent",
        hover_color=CORES["zebraEscura"],
        text_color=CORES["texto"],
        command=lambda: _ordenar_e_fechar(definir_ordenacao, coluna, True, ao_atualizar, _fechar),
    ).pack(fill="x", pady=(0, 8))

    ctk.CTkFrame(conteudo, height=1, fg_color=CORES["borda"]).pack(fill="x", pady=(0, 8))

    estado_limpar = "normal" if coluna_com_filtro_ativo(tabela, coluna) else "disabled"

    def _limpar_filtro() -> None:
        filtros[coluna] = None
        tabela._filtros_coluna = filtros  # type: ignore[attr-defined]
        ao_atualizar()
        _fechar()

    ctk.CTkButton(
        conteudo,
        text=f'Limpar filtro de "{rotulo_coluna}"',
        anchor="w",
        state=estado_limpar,
        fg_color="transparent",
        hover_color=CORES["zebraEscura"],
        text_color=CORES["texto"],
        command=_limpar_filtro,
    ).pack(fill="x", pady=(0, 8))

    campo_busca = ctk.CTkEntry(
        conteudo,
        placeholder_text="Pesquisar",
        fg_color=CORES["fundo"],
        border_color=CORES["borda"],
        text_color=CORES["texto"],
        placeholder_text_color=CORES["textoSecundario"],
    )
    campo_busca.pack(fill="x", pady=(0, 8))

    linha_botoes = ctk.CTkFrame(conteudo, fg_color="transparent")
    linha_botoes.pack(side="bottom", fill="x", pady=(10, 0))

    frame_lista = ctk.CTkScrollableFrame(
        conteudo,
        fg_color=CORES["fundo"],
        border_color=CORES["borda"],
        border_width=1,
        height=_ALTURA_LISTA,
        label_text="",
    )
    frame_lista.pack(fill="x", pady=(0, 4))

    vars_valores: dict[str, tk.BooleanVar] = {}
    widgets_valores: dict[str, ctk.CTkCheckBox] = {}
    var_todos = tk.BooleanVar(value=len(selecionados_iniciais) == len(valores_unicos))
    check_todos: ctk.CTkCheckBox | None = None

    def _valores_visiveis_busca() -> list[str]:
        termo = campo_busca.get().strip().casefold()
        if not termo:
            return list(valores_unicos)
        return [valor for valor in valores_unicos if termo in valor.casefold()]

    def _atualizar_var_todos() -> None:
        visiveis = _valores_visiveis_busca()
        if not visiveis:
            var_todos.set(False)
            return
        marcados = sum(1 for valor in visiveis if vars_valores[valor].get())
        if marcados == 0:
            var_todos.set(False)
        elif marcados == len(visiveis):
            var_todos.set(True)
        else:
            var_todos.set(False)

    def _ao_mudar_todos() -> None:
        marcar = var_todos.get()
        for valor in _valores_visiveis_busca():
            vars_valores[valor].set(marcar)

    def _ao_mudar_item() -> None:
        _atualizar_var_todos()

    def _montar_lista_opcoes() -> None:
        nonlocal check_todos
        for widget in frame_lista.winfo_children():
            widget.destroy()
        widgets_valores.clear()

        visiveis = _valores_visiveis_busca()
        check_todos = ctk.CTkCheckBox(
            frame_lista,
            text=_ROTULO_SELECIONAR_TUDO,
            variable=var_todos,
            command=_ao_mudar_todos,
            text_color=CORES["texto"],
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        )
        check_todos.pack(anchor="w", padx=8, pady=(6, 4))

        if not visiveis:
            ctk.CTkLabel(
                frame_lista,
                text="Nenhum valor encontrado.",
                text_color=CORES["textoSecundario"],
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=16, pady=4)
            var_todos.set(False)
            return

        for valor in visiveis:
            if valor not in vars_valores:
                vars_valores[valor] = tk.BooleanVar(value=valor in selecionados_iniciais)
            check = ctk.CTkCheckBox(
                frame_lista,
                text=valor,
                variable=vars_valores[valor],
                command=_ao_mudar_item,
                text_color=CORES["texto"],
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
            )
            check.pack(anchor="w", padx=16, pady=2)
            widgets_valores[valor] = check

        _atualizar_var_todos()
        frame_lista.update_idletasks()

    for valor in valores_unicos:
        vars_valores[valor] = tk.BooleanVar(value=valor in selecionados_iniciais)

    def _filtrar_lista_visivel(*_args: object) -> None:
        _montar_lista_opcoes()

    campo_busca.bind("<KeyRelease>", _filtrar_lista_visivel)
    _montar_lista_opcoes()

    def _confirmar() -> None:
        marcados = {valor for valor, var in vars_valores.items() if var.get()}
        todos = set(valores_unicos)
        if not marcados or marcados == todos:
            filtros[coluna] = None
        else:
            filtros[coluna] = marcados
        tabela._filtros_coluna = filtros  # type: ignore[attr-defined]
        ao_atualizar()
        _fechar()

    ctk.CTkButton(
        linha_botoes,
        text="Cancelar",
        width=100,
        fg_color=CORES["borda"],
        hover_color=CORES["zebraEscura"],
        text_color=CORES["texto"],
        command=_fechar,
    ).pack(side="right", padx=(8, 0))

    ctk.CTkButton(
        linha_botoes,
        text="OK",
        width=100,
        fg_color=CORES["primaria"],
        hover_color=CORES["primariaHover"],
        text_color=CORES["textoInverso"],
        command=_confirmar,
    ).pack(side="right")

    try:
        popup.grab_set()
    except tk.TclError:
        pass
    popup.after(50, lambda: campo_busca.focus_set())
    popup.focus_force()


def _ordenar_e_fechar(
    definir_ordenacao: Callable[[str, bool], None],
    coluna: str,
    descendente: bool,
    ao_atualizar: Callable[[], None],
    fechar: Callable[[], None],
) -> None:
    definir_ordenacao(coluna, descendente)
    ao_atualizar()
    fechar()


def _linha_passa_filtros(
    linha: Any,
    filtros: dict[str, set[str] | None],
    obter_valor: Callable[[Any, str], str],
) -> bool:
    for coluna, selecionados in filtros.items():
        if selecionados is None:
            continue
        valor = _normalizar_valor_filtro(obter_valor(linha, coluna))
        if valor not in selecionados:
            return False
    return True


def _valores_unicos_coluna(
    linhas: Iterable[T],
    coluna: str,
    obter_valor: Callable[[T, str], str],
) -> list[str]:
    vistos: set[str] = set()
    ordenados: list[str] = []
    for linha in linhas:
        valor = _normalizar_valor_filtro(obter_valor(linha, coluna))
        if valor in vistos:
            continue
        vistos.add(valor)
        ordenados.append(valor)
    return sorted(ordenados, key=lambda texto: texto.casefold())


def _normalizar_valor_filtro(texto: str) -> str:
    limpo = (texto or "").strip()
    return limpo if limpo else _VALOR_VAZIO


def _calcular_posicao_popup(tabela: ttk.Treeview, coluna: str) -> tuple[int, int]:
    try:
        x = tabela.winfo_rootx()
        y = tabela.winfo_rooty()
        offset = 0
        for col in tabela["columns"]:
            if col == coluna:
                break
            offset += int(tabela.column(col, "width"))
        largura_popup = _LARGURA_POPUP
        largura_tela = tabela.winfo_screenwidth()
        altura_tela = tabela.winfo_screenheight()
        pos_x = min(max(0, x + offset), max(0, largura_tela - largura_popup - 8))
        pos_y = min(y + 28, max(0, altura_tela - 440))
        return pos_x, pos_y
    except tk.TclError:
        return 100, 100
