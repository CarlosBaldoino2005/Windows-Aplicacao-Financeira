"""Grid da carteira de investimentos com ordenacao por coluna."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from src.Model.carteira import ROTULOS_TIPO_CARTEIRA, LinhaCarteira
from src.Model.opcoes_fonte_grid import OpcoesFonteGrid
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.View.formatadores import formatar_moeda, formatar_texto_opcional
from src.View.grid_ordenacao_helper import SUFIXO_ASCENDENTE, SUFIXO_DESCENDENTE, chave_comparavel
from src.View.grid_interacao_treeview_helper import (
    aplicar_destaque_estilo_treeview,
    aplicar_destaque_tags_treeview,
    configurar_interacao_treeview,
    liberar_interacao_treeview,
    obter_iid_linha_evento_treeview,
    sincronizar_tags_selecao_treeview,
    treeview_ainda_ativa,
)
from src.View.tema import CORES

_COLUNAS = (
    "tipo",
    "ativo",
    "nome",
    "quantidade",
    "data_compra",
    "preco_compra",
    "investido",
    "preco_atual",
    "valor_atual",
    "resultado_pct",
    "resultado_reais",
    "dividendos",
    "prox_dividendo",
)
_ROTULOS = {
    "tipo": "Tipo",
    "ativo": "Ativo",
    "nome": "Nome",
    "quantidade": "Qtd",
    "data_compra": "Compra",
    "preco_compra": "Preco compra",
    "investido": "Investido",
    "preco_atual": "Preco atual",
    "valor_atual": "Valor atual",
    "resultado_pct": "Valoriz. %",
    "resultado_reais": "Valoriz. R$",
    "dividendos": "Dividendos",
    "prox_dividendo": "Prox. dividendo",
}
_LARGURAS = (90, 80, 160, 70, 90, 100, 100, 100, 100, 90, 100, 100, 130)
_FONTE_FAMILIA = "Segoe UI"


def _formatar_quantidade(valor: float) -> str:
    texto = f"{valor:.8f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def _formatar_resultado_pct(valor: float | None) -> str:
    if valor is None:
        return "—"
    sinal = "+" if valor >= 0 else ""
    return f"{sinal}{valor:.2f}%"


def _resolver_opcoes(opcoes: OpcoesFonteGrid | None) -> OpcoesFonteGrid:
    if opcoes is not None:
        return opcoes
    return ConfigPainelIni().carregar_opcoes_fonte_grid()


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
            command=lambda c=coluna: _alternar_ordenacao_carteira(tabela, c),
        )


def _configurar_ordenacao_colunas(tabela: ttk.Treeview) -> None:
    if getattr(tabela, "_ordenacao_configurada", False):
        return
    tabela._ordenacao_configurada = True  # type: ignore[attr-defined]
    tabela._coluna_ordenacao = None  # type: ignore[attr-defined]
    tabela._ordenacao_desc = False  # type: ignore[attr-defined]
    tabela._linhas_originais: list[LinhaCarteira] = []  # type: ignore[attr-defined]

    for coluna in _COLUNAS:
        tabela.heading(
            coluna,
            text=_ROTULOS[coluna],
            command=lambda c=coluna: _alternar_ordenacao_carteira(tabela, c),
        )


def _alternar_ordenacao_carteira(tabela: ttk.Treeview, coluna: str) -> None:
    if getattr(tabela, "_coluna_ordenacao", None) == coluna:
        tabela._ordenacao_desc = not getattr(tabela, "_ordenacao_desc", False)  # type: ignore[attr-defined]
    else:
        tabela._coluna_ordenacao = coluna  # type: ignore[attr-defined]
        tabela._ordenacao_desc = False  # type: ignore[attr-defined]

    linhas = list(getattr(tabela, "_linhas_originais", []))
    preencher_grid_carteira(tabela, linhas)


def _chave_ordenacao_linha(linha: LinhaCarteira, coluna: str) -> tuple:
    posicao = linha.posicao
    cotacao = linha.cotacao
    moeda = cotacao.moeda if cotacao is not None else "BRL"

    if coluna == "tipo":
        return chave_comparavel(ROTULOS_TIPO_CARTEIRA.get(posicao.tipo_ativo, posicao.tipo_ativo))
    if coluna == "ativo":
        return chave_comparavel(codigo_exibicao(posicao.simbolo))
    if coluna == "nome":
        return chave_comparavel(cotacao.nome if cotacao is not None else None)
    if coluna == "quantidade":
        return chave_comparavel(posicao.quantidade)
    if coluna == "data_compra":
        return chave_comparavel(posicao.data_compra)
    if coluna == "preco_compra":
        return chave_comparavel(posicao.preco_compra)
    if coluna == "investido":
        return chave_comparavel(posicao.valor_investido)
    if coluna == "preco_atual":
        return chave_comparavel(linha.preco_atual)
    if coluna == "valor_atual":
        return chave_comparavel(linha.valor_atual)
    if coluna == "resultado_pct":
        return chave_comparavel(linha.resultado_percentual)
    if coluna == "resultado_reais":
        return chave_comparavel(linha.resultado_reais)
    if coluna == "dividendos":
        return chave_comparavel(linha.dividendos_recebidos)
    if coluna == "prox_dividendo":
        texto = linha.proximo_dividendo_data
        if linha.proximo_dividendo_previsto is not None:
            texto = f"{texto} {formatar_moeda(linha.proximo_dividendo_previsto, moeda)}"
        return chave_comparavel(texto)
    return chave_comparavel("")


def _ordenar_linhas_carteira(
    linhas: list[LinhaCarteira],
    coluna: str | None,
    descendente: bool,
) -> list[LinhaCarteira]:
    if not coluna or not linhas:
        return linhas
    return sorted(
        linhas,
        key=lambda linha: _chave_ordenacao_linha(linha, coluna),
        reverse=descendente,
    )


def _tag_resultado(linha: LinhaCarteira, indice: int) -> str:
    resultado = linha.resultado_reais
    if resultado is None:
        return "normal_par" if indice % 2 == 0 else "normal_impar"
    if resultado > 0:
        return "positivo"
    if resultado < 0:
        return "negativo"
    return "normal_par" if indice % 2 == 0 else "normal_impar"


def obter_id_duplo_clique_carteira(tabela: ttk.Treeview, evento) -> str | None:
    return obter_iid_linha_evento_treeview(tabela, evento)


def criar_grid_carteira(
    pai: ctk.CTkBaseClass,
    titulo: str,
    *,
    altura: int = 16,
    ao_duplo_clique: Callable | None = None,
) -> ttk.Treeview:
    card = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=12)
    card.pack(fill="both", expand=True)

    ctk.CTkLabel(
        card,
        text=titulo,
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=CORES["texto"],
    ).pack(anchor="w", padx=12, pady=(12, 4))

    ctk.CTkLabel(
        card,
        text="Duplo clique abre o grafico. Verde = valorizacao; vermelho = desvalorizacao.",
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
    scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela.yview)
    scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=tabela.xview)
    tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    tabela.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")
    scroll_x.pack(side="bottom", fill="x")

    _configurar_ordenacao_colunas(tabela)

    for coluna, largura in zip(_COLUNAS, _LARGURAS, strict=True):
        tabela.column(coluna, width=largura, anchor="w", stretch=False)

    aplicar_estilo_grid_carteira(tabela)
    configurar_interacao_treeview(tabela, ao_duplo_clique=ao_duplo_clique)

    label_vazio = ctk.CTkLabel(
        card,
        text="Nenhuma posicao na carteira. Clique em Registrar compra.",
        font=ctk.CTkFont(size=13),
        text_color=CORES["textoSecundario"],
    )
    label_vazio.pack(pady=(0, 12))
    label_vazio.pack_forget()

    tabela._card_pai = card  # type: ignore[attr-defined]
    tabela._label_vazio = label_vazio  # type: ignore[attr-defined]
    return tabela


def aplicar_estilo_grid_carteira(
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
        "positivo",
        background=CORES.get("sucessoFundo", "#F0FDF4"),
        foreground=CORES.get("sucesso", "#16A34A"),
    )
    tabela.tag_configure(
        "negativo",
        background=CORES.get("erroFundo", "#FEF2F2"),
        foreground=CORES.get("erro", "#DC2626"),
    )
    aplicar_destaque_tags_treeview(tabela)


def preencher_grid_carteira(
    tabela: ttk.Treeview,
    linhas: list[LinhaCarteira],
) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    _configurar_ordenacao_colunas(tabela)
    tabela._linhas_originais = list(linhas)  # type: ignore[attr-defined]

    coluna_ord = getattr(tabela, "_coluna_ordenacao", None)
    descendente = getattr(tabela, "_ordenacao_desc", False)
    linhas_exibir = _ordenar_linhas_carteira(linhas, coluna_ord, descendente)

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
            label_vazio.pack(pady=(0, 12))
        tabela.selection_set()
        _atualizar_cabecalhos_ordenacao(tabela)
        return

    if label_vazio is not None:
        label_vazio.pack_forget()

    aplicar_estilo_grid_carteira(tabela)

    for indice, linha in enumerate(linhas_exibir):
        posicao = linha.posicao
        cotacao = linha.cotacao
        moeda = cotacao.moeda if cotacao is not None else "BRL"
        preco_atual_texto = (
            formatar_moeda(linha.preco_atual, moeda)
            if linha.preco_atual is not None
            else "—"
        )
        valor_atual_texto = (
            formatar_moeda(linha.valor_atual, moeda)
            if linha.valor_atual is not None
            else "—"
        )
        resultado_reais_texto = (
            formatar_moeda(linha.resultado_reais, moeda)
            if linha.resultado_reais is not None
            else "—"
        )

        prox_texto = formatar_texto_opcional(linha.proximo_dividendo_data)
        if linha.proximo_dividendo_previsto is not None and linha.proximo_dividendo_data:
            prox_texto = (
                f"{linha.proximo_dividendo_data} — "
                f"{formatar_moeda(linha.proximo_dividendo_previsto, moeda)}"
            )

        tag = _tag_resultado(linha, indice)
        tabela._tags_zebra[posicao.id] = tag  # type: ignore[attr-defined]
        tabela.insert(
            "",
            "end",
            iid=posicao.id,
            values=(
                ROTULOS_TIPO_CARTEIRA.get(posicao.tipo_ativo, posicao.tipo_ativo),
                codigo_exibicao(posicao.simbolo),
                cotacao.nome if cotacao is not None else "—",
                _formatar_quantidade(posicao.quantidade),
                posicao.data_compra,
                formatar_moeda(posicao.preco_compra, moeda),
                formatar_moeda(posicao.valor_investido, moeda),
                preco_atual_texto,
                valor_atual_texto,
                _formatar_resultado_pct(linha.resultado_percentual),
                resultado_reais_texto,
                formatar_moeda(linha.dividendos_recebidos, moeda),
                prox_texto,
            ),
            tags=(tag,),
        )

    iids_visiveis = {linha.posicao.id for linha in linhas_exibir}
    selecionados_depois = tuple(selecionados_antes & iids_visiveis)
    if selecionados_depois:
        tabela.selection_set(selecionados_depois)
    else:
        tabela.selection_set()
    sincronizar_tags_selecao_treeview(tabela)
    _atualizar_cabecalhos_ordenacao(tabela)


def liberar_grid_carteira(tabela: ttk.Treeview | None) -> None:
    liberar_interacao_treeview(tabela)
