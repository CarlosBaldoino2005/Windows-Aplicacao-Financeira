"""Grid de IPOs recentes com ordenacao e filtro por coluna."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk

from src.Model.ipo_recente import LinhaIpoRecente
from src.Model.opcoes_fonte_grid import OpcoesFonteGrid
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.View.formatadores import formatar_moeda, formatar_preco_negocio
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

_COLUNAS = (
    "data_ipo",
    "simbolo",
    "nome",
    "mercado",
    "na_b3",
    "abriu_hoje",
    "preco_ipo",
    "preco_atual",
    "var_ipo",
    "baixa_dia",
    "hora_baixa",
    "var_baixa",
    "alta_dia",
    "hora_alta",
    "var_alta",
    "fechamento_dia",
)
_ROTULOS = {
    "data_ipo": "Data IPO",
    "simbolo": "Sigla",
    "nome": "Empresa",
    "mercado": "Mercado",
    "na_b3": "Na B3",
    "abriu_hoje": "Abriu hoje",
    "preco_ipo": "Preco abertura",
    "preco_atual": "Preco atual",
    "var_ipo": "Var. desde IPO",
    "baixa_dia": "Baixa do dia",
    "hora_baixa": "Hora baixa",
    "var_baixa": "Var. na baixa",
    "alta_dia": "Alta do dia",
    "hora_alta": "Hora alta",
    "var_alta": "Var. na alta",
    "fechamento_dia": "Fechamento",
}
_LARGURAS = (
    105,  # data_ipo
    88,   # simbolo
    300,  # nome
    118,  # mercado
    82,   # na_b3
    102,  # abriu_hoje
    135,  # preco_ipo
    118,  # preco_atual
    128,  # var_ipo
    112,  # baixa_dia
    98,   # hora_baixa
    118,  # var_baixa
    112,  # alta_dia
    98,   # hora_alta
    118,  # var_alta
    118,  # fechamento_dia
)
_FONTE_FAMILIA = "Segoe UI"
_ESTILO_TREEVIEW = "Ipos.Treeview"


def _resolver_opcoes(opcoes: OpcoesFonteGrid | None) -> OpcoesFonteGrid:
    if opcoes is not None:
        return opcoes
    return ConfigPainelIni().carregar_opcoes_fonte_grid()


def _formatar_pct(valor: float | None) -> str:
    if valor is None:
        return "—"
    sinal = "+" if valor >= 0 else ""
    return f"{sinal}{valor:.2f}%"


def _texto_sigla_ipo(linha: LinhaIpoRecente) -> str:
    sigla_ipo = codigo_exibicao(linha.simbolo)
    if linha.simbolo_b3:
        sigla_b3 = codigo_exibicao(linha.simbolo_b3)
        if sigla_b3 != sigla_ipo:
            return f"{sigla_ipo} ({sigla_b3})"
    return sigla_ipo


def _textos_linha_ipo(linha: LinhaIpoRecente) -> dict[str, str]:
    moeda = linha.moeda
    return {
        "data_ipo": linha.data_ipo.strftime("%d/%m/%Y"),
        "simbolo": _texto_sigla_ipo(linha),
        "nome": linha.nome,
        "mercado": linha.mercado,
        "na_b3": "Sim" if linha.na_b3 else "Nao",
        "abriu_hoje": "Sim" if linha.abriu_hoje else "Nao",
        "preco_ipo": (
            formatar_moeda(linha.preco_abertura_capital, moeda)
            if linha.preco_abertura_capital is not None
            else "—"
        ),
        "preco_atual": (
            formatar_moeda(linha.preco_atual, moeda) if linha.preco_atual is not None else "—"
        ),
        "var_ipo": _formatar_pct(linha.variacao_desde_ipo_pct),
        "baixa_dia": formatar_preco_negocio(linha.preco_baixa_dia),
        "hora_baixa": linha.hora_baixa_dia or "—",
        "var_baixa": _formatar_pct(linha.variacao_baixa_dia_pct),
        "alta_dia": formatar_preco_negocio(linha.preco_alta_dia),
        "hora_alta": linha.hora_alta_dia or "—",
        "var_alta": _formatar_pct(linha.variacao_alta_dia_pct),
        "fechamento_dia": (
            formatar_moeda(linha.preco_fechamento_dia, moeda)
            if linha.preco_fechamento_dia is not None
            else "—"
        ),
    }


def _chave_coluna_ipo(linha: LinhaIpoRecente, coluna: str):
    if coluna == "data_ipo":
        return linha.data_ipo.toordinal()
    if coluna == "simbolo":
        return linha.simbolo.lower()
    if coluna == "nome":
        return linha.nome.lower()
    if coluna == "mercado":
        return linha.mercado.lower()
    if coluna == "na_b3":
        return linha.na_b3
    if coluna == "abriu_hoje":
        return linha.abriu_hoje
    if coluna == "preco_ipo":
        return linha.preco_abertura_capital or 0
    if coluna == "preco_atual":
        return linha.preco_atual or 0
    if coluna == "var_ipo":
        return linha.variacao_desde_ipo_pct or 0
    if coluna == "baixa_dia":
        return linha.preco_baixa_dia or 0
    if coluna == "hora_baixa":
        return linha.hora_baixa_dia or ""
    if coluna == "var_baixa":
        return linha.variacao_baixa_dia_pct or 0
    if coluna == "alta_dia":
        return linha.preco_alta_dia or 0
    if coluna == "hora_alta":
        return linha.hora_alta_dia or ""
    if coluna == "var_alta":
        return linha.variacao_alta_dia_pct or 0
    if coluna == "fechamento_dia":
        return linha.preco_fechamento_dia or 0
    return ""


def _configurar_ordenacao_colunas(tabela: ttk.Treeview) -> None:
    if getattr(tabela, "_ordenacao_configurada", False):
        return
    tabela._ordenacao_configurada = True  # type: ignore[attr-defined]
    tabela._coluna_ordenacao = "data_ipo"  # type: ignore[attr-defined]
    tabela._ordenacao_desc = True  # type: ignore[attr-defined]
    tabela._itens_originais: list[LinhaIpoRecente] = []  # type: ignore[attr-defined]
    inicializar_filtros_coluna_treeview(tabela)
    _atualizar_cabecalhos_ipos(tabela)


def aplicar_estilo_grid_ipos(
    tabela: ttk.Treeview,
    opcoes_fonte: OpcoesFonteGrid | None = None,
) -> None:
    """Aplica tema, zebrado e fonte no padrao das demais grids do projeto."""
    if not treeview_ainda_ativa(tabela):
        return

    opcoes = _resolver_opcoes(opcoes_fonte)
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure(
        _ESTILO_TREEVIEW,
        background=CORES["zebraClara"],
        fieldbackground=CORES["zebraClara"],
        foreground=CORES["texto"],
        borderwidth=0,
        rowheight=opcoes.altura_linha,
        font=(_FONTE_FAMILIA, opcoes.fonte_tree),
    )
    estilo.configure(
        f"{_ESTILO_TREEVIEW}.Heading",
        background=CORES["zebraEscura"],
        foreground=CORES["texto"],
        font=(_FONTE_FAMILIA, opcoes.fonte_cabecalho_tree, "bold"),
        relief="flat",
    )
    estilo.layout(_ESTILO_TREEVIEW, estilo.layout("Treeview"))
    tabela.configure(style=_ESTILO_TREEVIEW)
    aplicar_destaque_estilo_treeview(estilo)

    tabela.tag_configure("par", background=CORES["zebraClara"], foreground=CORES["texto"])
    tabela.tag_configure("impar", background=CORES["zebraEscura"], foreground=CORES["texto"])
    aplicar_destaque_tags_treeview(tabela)

    for coluna, largura in zip(_COLUNAS, _LARGURAS, strict=True):
        tabela.column(coluna, width=largura, minwidth=largura, stretch=False, anchor="w")

    label_titulo = getattr(tabela, "_label_titulo_card", None)
    if label_titulo is not None:
        label_titulo.configure(font=ctk.CTkFont(size=opcoes.fonte_titulo_card, weight="bold"))

    label_vazio = getattr(tabela, "_label_vazio", None)
    if label_vazio is not None:
        label_vazio.configure(font=ctk.CTkFont(size=opcoes.fonte_mensagem_vazio))


def criar_tabela_ipos(
    pai: ctk.CTkBaseClass,
    titulo: str,
    altura: int = 16,
    expandir: bool = True,
    opcoes_fonte: OpcoesFonteGrid | None = None,
) -> ttk.Treeview:
    opcoes = _resolver_opcoes(opcoes_fonte)
    card = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=12)
    if expandir:
        card.pack(fill="both", expand=True, pady=8)
    else:
        card.pack(fill="x", pady=8)

    linha_titulo = ctk.CTkFrame(card, fg_color="transparent")
    linha_titulo.pack(fill="x", padx=12, pady=(12, 4))

    label_titulo = ctk.CTkLabel(
        linha_titulo,
        text=titulo,
        font=ctk.CTkFont(size=opcoes.fonte_titulo_card, weight="bold"),
        text_color=CORES["texto"],
    )
    label_titulo.pack(side="left", anchor="w")
    frame_botoes = criar_frame_botoes_titulo_grid(linha_titulo)

    frame_tabela = ctk.CTkFrame(card, fg_color="transparent")
    frame_tabela.pack(fill="both", expand=expandir, padx=12, pady=(0, 8))
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
    aplicar_estilo_grid_ipos(tabela, opcoes)
    configurar_interacao_treeview(tabela)

    label_vazio = ctk.CTkLabel(
        card,
        text="Nenhum IPO no periodo.",
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
    vincular_botao_exportar_treeview(frame_botoes, tabela, titulo, janela_pai=card)
    return tabela


def _atualizar_cabecalhos_ipos(tabela: ttk.Treeview) -> None:
    atualizar_cabecalhos_com_filtro_treeview(
        tabela,
        _COLUNAS,
        lambda coluna: _ROTULOS[coluna],
        lambda coluna: _abrir_filtro_coluna_ipos(tabela, coluna),
    )


def _abrir_filtro_coluna_ipos(tabela: ttk.Treeview, coluna: str) -> None:
    abrir_popup_filtro_coluna_treeview(
        tabela=tabela,
        coluna=coluna,
        rotulo_coluna=_ROTULOS[coluna],
        linhas=list(getattr(tabela, "_itens_originais", [])),
        obter_valor=lambda linha, c=coluna: _textos_linha_ipo(linha)[c],
        ao_atualizar=lambda: _renderizar_tabela_ipos(tabela),
        definir_ordenacao=lambda col, desc: _definir_ordenacao_ipos(tabela, col, desc),
    )


def _definir_ordenacao_ipos(tabela: ttk.Treeview, coluna: str, descendente: bool) -> None:
    tabela._coluna_ordenacao = coluna  # type: ignore[attr-defined]
    tabela._ordenacao_desc = descendente  # type: ignore[attr-defined]


def preencher_tabela_ipos(
    tabela: ttk.Treeview,
    itens: list[LinhaIpoRecente],
    mensagem_vazio: str | None = None,
) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    _configurar_ordenacao_colunas(tabela)
    tabela._itens_originais = list(itens)  # type: ignore[attr-defined]
    if mensagem_vazio:
        tabela._mensagem_vazio = mensagem_vazio  # type: ignore[attr-defined]
    _renderizar_tabela_ipos(tabela)


def _renderizar_tabela_ipos(tabela: ttk.Treeview) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    itens_originais = list(getattr(tabela, "_itens_originais", []))
    itens = aplicar_filtros_coluna_treeview(
        itens_originais,
        tabela,
        lambda linha, coluna: _textos_linha_ipo(linha)[coluna],
    )

    coluna = getattr(tabela, "_coluna_ordenacao", "data_ipo")
    descendente = getattr(tabela, "_ordenacao_desc", True)
    itens.sort(
        key=lambda linha: _chave_coluna_ipo(linha, coluna),
        reverse=descendente,
    )
    _atualizar_cabecalhos_ipos(tabela)

    selecionados = set(tabela.selection())
    liberar_interacao_treeview(tabela)
    tabela._tags_zebra = {}  # type: ignore[attr-defined]

    filhos = tabela.get_children()
    if filhos:
        tabela.delete(*filhos)

    if itens:
        aplicar_estilo_grid_ipos(tabela)
        tags_zebra = ("par", "impar")
        for indice, linha in enumerate(itens):
            textos = _textos_linha_ipo(linha)
            valores = tuple(textos[c] for c in _COLUNAS)
            tag = tags_zebra[indice % 2]
            iid = linha.simbolo
            tabela._tags_zebra[iid] = tag  # type: ignore[attr-defined]
            tabela.insert("", "end", iid=iid, values=valores, tags=(tag,))

    label_vazio = getattr(tabela, "_label_vazio", None)
    if label_vazio is not None:
        if itens:
            label_vazio.pack_forget()
        else:
            if itens_originais:
                label_vazio.configure(text="Nenhum IPO corresponde aos filtros atuais.")
            else:
                msg = getattr(tabela, "_mensagem_vazio", "Nenhum IPO no periodo.")
                label_vazio.configure(text=msg)
            label_vazio.pack(fill="x", padx=12, pady=(0, 12))

    if selecionados:
        existentes = [iid for iid in selecionados if tabela.exists(iid)]
        if existentes:
            tabela.selection_set(existentes)

    sincronizar_tags_selecao_treeview(tabela)


def reaplicar_fonte_tabela_ipos(tabela: ttk.Treeview | None) -> None:
    if tabela is None or not treeview_ainda_ativa(tabela):
        return
    aplicar_estilo_grid_ipos(tabela)
