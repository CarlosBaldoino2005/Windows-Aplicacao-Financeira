"""Grid de monitoramento de precos com destaque por limites."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from src.Model.monitoramento import (
    ROTULOS_STATUS,
    ROTULOS_TIPO_ATIVO,
    MonitoramentoLinha,
    StatusMonitoramento,
)
from src.Model.opcoes_fonte_grid import OpcoesFonteGrid
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.View.formatadores import formatar_moeda
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
    obter_iid_linha_evento_treeview,
    sincronizar_tags_selecao_treeview,
    treeview_ainda_ativa,
)
from src.View.exportar_xlsx_grid_helper import (
    criar_frame_botoes_titulo_grid,
    vincular_botao_exportar_treeview,
)
from src.View.tema import CORES, obter_modo_aparencia

_COLUNAS = (
    "tipo",
    "ativo",
    "nome",
    "preco_atual",
    "valor_baixo",
    "valor_alto",
    "status",
)
_ROTULOS = {
    "tipo": "Tipo",
    "ativo": "Ativo",
    "nome": "Nome",
    "preco_atual": "Preco atual",
    "valor_baixo": "Valor baixo",
    "valor_alto": "Valor alto",
    "status": "Status",
}
_LARGURAS = (130, 90, 220, 110, 110, 110, 140)
_FONTE_FAMILIA = "Segoe UI"
_TAG_POR_STATUS: dict[StatusMonitoramento, str] = {
    "normal": "normal_par",
    "abaixo": "alerta_baixo",
    "acima": "alerta_alto",
    "indisponivel": "indisponivel",
    "pausado": "pausado",
}


def _obter_cores_pausado() -> tuple[str, str, str]:
    """
    Cores mais claras e apagadas para itens pausados (nao monitorados).
    Retorna (fundo_par, fundo_impar, texto).
    """
    if obter_modo_aparencia() == "escuro":
        return "#3A4552", "#424E5C", "#8B98A8"
    return "#E8EDF3", "#DFE6EE", "#8A96A6"


def _resolver_opcoes(opcoes: OpcoesFonteGrid | None) -> OpcoesFonteGrid:
    if opcoes is not None:
        return opcoes
    return ConfigPainelIni().carregar_opcoes_fonte_grid()


def _textos_linha_monitoramento(linha: MonitoramentoLinha) -> dict[str, str]:
    cotacao = linha.cotacao
    moeda = cotacao.moeda if cotacao is not None else "BRL"
    preco_texto = (
        formatar_moeda(cotacao.preco, moeda)
        if cotacao is not None and cotacao.preco > 0
        else "—"
    )
    nome = cotacao.nome if cotacao is not None else "—"
    return {
        "tipo": ROTULOS_TIPO_ATIVO.get(linha.item.tipo_ativo, linha.item.tipo_ativo),
        "ativo": codigo_exibicao(linha.item.simbolo),
        "nome": nome,
        "preco_atual": preco_texto,
        "valor_baixo": formatar_moeda(linha.item.valor_baixo, moeda)
        if linha.item.valor_baixo is not None
        else "—",
        "valor_alto": formatar_moeda(linha.item.valor_alto, moeda)
        if linha.item.valor_alto is not None
        else "—",
        "status": ROTULOS_STATUS.get(linha.status, linha.status),
    }


def _valor_celula_monitoramento(linha: MonitoramentoLinha, coluna: str) -> str:
    return _textos_linha_monitoramento(linha).get(coluna, "")


def _atualizar_cabecalhos_ordenacao(tabela: ttk.Treeview) -> None:
    atualizar_cabecalhos_com_filtro_treeview(
        tabela,
        _COLUNAS,
        _ROTULOS,
        lambda coluna: _abrir_filtro_coluna_monitoramento(tabela, coluna),
    )


def _abrir_filtro_coluna_monitoramento(tabela: ttk.Treeview, coluna: str) -> None:
    abrir_popup_filtro_coluna_treeview(
        tabela=tabela,
        coluna=coluna,
        rotulo_coluna=_ROTULOS.get(coluna, coluna),
        linhas=list(getattr(tabela, "_linhas_originais", [])),
        obter_valor=_valor_celula_monitoramento,
        ao_atualizar=lambda: _renderizar_grid_monitoramento(tabela),
        definir_ordenacao=lambda col, desc: _definir_ordenacao_monitoramento(tabela, col, desc),
    )


def _definir_ordenacao_monitoramento(tabela: ttk.Treeview, coluna: str, descendente: bool) -> None:
    tabela._coluna_ordenacao = coluna  # type: ignore[attr-defined]
    tabela._ordenacao_desc = descendente  # type: ignore[attr-defined]


def _configurar_ordenacao_colunas(tabela: ttk.Treeview) -> None:
    if getattr(tabela, "_ordenacao_configurada", False):
        return
    tabela._ordenacao_configurada = True  # type: ignore[attr-defined]
    tabela._coluna_ordenacao = None  # type: ignore[attr-defined]
    tabela._ordenacao_desc = False  # type: ignore[attr-defined]
    tabela._linhas_originais: list[MonitoramentoLinha] = []  # type: ignore[attr-defined]
    inicializar_filtros_coluna_treeview(tabela)
    _atualizar_cabecalhos_ordenacao(tabela)


def _chave_ordenacao_linha(linha: MonitoramentoLinha, coluna: str) -> tuple:
    cotacao = linha.cotacao
    if coluna == "tipo":
        return chave_comparavel(
            ROTULOS_TIPO_ATIVO.get(linha.item.tipo_ativo, linha.item.tipo_ativo)
        )
    if coluna == "ativo":
        return chave_comparavel(codigo_exibicao(linha.item.simbolo))
    if coluna == "nome":
        return chave_comparavel(cotacao.nome if cotacao is not None else None)
    if coluna == "preco_atual":
        preco = cotacao.preco if cotacao is not None and cotacao.preco > 0 else None
        return chave_comparavel(preco)
    if coluna == "valor_baixo":
        return chave_comparavel(linha.item.valor_baixo)
    if coluna == "valor_alto":
        return chave_comparavel(linha.item.valor_alto)
    if coluna == "status":
        return chave_comparavel(ROTULOS_STATUS.get(linha.status, linha.status))
    return chave_comparavel("")


def _ordenar_linhas_monitoramento(
    linhas: list[MonitoramentoLinha],
    coluna: str | None,
    descendente: bool,
) -> list[MonitoramentoLinha]:
    if not coluna or not linhas:
        return linhas
    return sorted(
        linhas,
        key=lambda linha: _chave_ordenacao_linha(linha, coluna),
        reverse=descendente,
    )


def obter_id_duplo_clique_monitoramento(tabela: ttk.Treeview, evento) -> str | None:
    """Retorna o id do item monitorado na linha do duplo clique."""
    return obter_iid_linha_evento_treeview(tabela, evento)


def criar_grid_monitoramento(
    pai: ctk.CTkBaseClass,
    titulo: str,
    *,
    altura: int = 16,
    ao_duplo_clique: Callable | None = None,
) -> ttk.Treeview:
    """Cria card com grid zebrada e tags de alerta."""
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
        text="Clique no titulo da coluna para filtrar e ordenar. Duplo clique abre grafico.",
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

    for coluna, largura in zip(_COLUNAS, _LARGURAS, strict=True):
        tabela.column(coluna, width=largura, anchor="w")

    aplicar_estilo_grid_monitoramento(tabela)
    configurar_interacao_treeview(tabela, ao_duplo_clique=ao_duplo_clique)

    label_vazio = ctk.CTkLabel(
        card,
        text="Nenhum ativo em monitoramento. Clique em Adicionar monitoramento.",
        font=ctk.CTkFont(size=13),
        text_color=CORES["textoSecundario"],
    )
    label_vazio.pack(pady=(0, 12))
    label_vazio.pack_forget()

    tabela._card_pai = card  # type: ignore[attr-defined]
    tabela._label_vazio = label_vazio  # type: ignore[attr-defined]
    vincular_botao_exportar_treeview(frame_botoes, tabela, titulo, janela_pai=card)
    return tabela


def aplicar_estilo_grid_monitoramento(
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
    tabela.tag_configure(
        "alerta_baixo",
        background=CORES.get("erroFundo", "#FEF2F2"),
        foreground=CORES.get("erro", "#DC2626"),
    )
    tabela.tag_configure(
        "alerta_alto",
        background=CORES.get("sucessoFundo", "#F0FDF4"),
        foreground=CORES.get("sucesso", "#16A34A"),
    )
    tabela.tag_configure(
        "indisponivel",
        background=CORES["zebraEscura"],
        foreground=CORES["textoSecundario"],
    )
    fundo_pausado_par, fundo_pausado_impar, texto_pausado = _obter_cores_pausado()
    tabela.tag_configure("pausado", background=fundo_pausado_par, foreground=texto_pausado)
    tabela.tag_configure("pausado_par", background=fundo_pausado_par, foreground=texto_pausado)
    tabela.tag_configure(
        "pausado_impar",
        background=fundo_pausado_impar,
        foreground=texto_pausado,
    )
    aplicar_destaque_tags_treeview(tabela)


def preencher_grid_monitoramento(
    tabela: ttk.Treeview,
    linhas: list[MonitoramentoLinha],
) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    _configurar_ordenacao_colunas(tabela)
    tabela._linhas_originais = list(linhas)  # type: ignore[attr-defined]
    _renderizar_grid_monitoramento(tabela)


def _renderizar_grid_monitoramento(tabela: ttk.Treeview) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    linhas_originais = list(getattr(tabela, "_linhas_originais", []))
    linhas = aplicar_filtros_coluna_treeview(linhas_originais, tabela, _valor_celula_monitoramento)
    coluna_ord = getattr(tabela, "_coluna_ordenacao", None)
    descendente = getattr(tabela, "_ordenacao_desc", False)
    linhas_exibir = _ordenar_linhas_monitoramento(linhas, coluna_ord, descendente)
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

    if not linhas_exibir:
        if label_vazio is not None:
            if linhas_originais:
                label_vazio.configure(text="Nenhum ativo corresponde aos filtros atuais.")
            else:
                label_vazio.configure(
                    text="Nenhum ativo em monitoramento. Clique em Adicionar monitoramento.",
                )
            label_vazio.pack(pady=(0, 12))
        tabela.selection_set()
        return

    if label_vazio is not None:
        label_vazio.pack_forget()

    aplicar_estilo_grid_monitoramento(tabela)

    for indice, linha in enumerate(linhas_exibir):
        textos = _textos_linha_monitoramento(linha)
        tag_base = _TAG_POR_STATUS[linha.status]
        if linha.status == "normal":
            tag = "normal_par" if indice % 2 == 0 else "normal_impar"
        elif linha.status == "pausado":
            tag = "pausado_par" if indice % 2 == 0 else "pausado_impar"
        else:
            tag = tag_base

        tabela._tags_zebra[linha.item.id] = tag  # type: ignore[attr-defined]
        tabela.insert(
            "",
            "end",
            iid=linha.item.id,
            values=tuple(textos[col] for col in _COLUNAS),
            tags=(tag,),
        )

    iids_visiveis = {linha.item.id for linha in linhas_exibir}
    selecionados_depois = tuple(selecionados_antes & iids_visiveis)
    if selecionados_depois:
        tabela.selection_set(selecionados_depois)
    else:
        tabela.selection_set()
    sincronizar_tags_selecao_treeview(tabela)


def liberar_grid_monitoramento(tabela: ttk.Treeview | None) -> None:
    liberar_interacao_treeview(tabela)
