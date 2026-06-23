"""Grid do historico de compras da carteira com ordenacao por coluna."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk

from src.Model.carteira import ROTULOS_TIPO_CARTEIRA, LinhaCompraCarteira
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
    configurar_interacao_treeview,
    liberar_interacao_treeview,
    sincronizar_tags_selecao_treeview,
    treeview_ainda_ativa,
)
from src.View.exportar_xlsx_grid_helper import (
    criar_frame_botoes_titulo_grid,
    vincular_botao_exportar_treeview,
)
from src.View.tabela_carteira_helper import (
    aplicar_ajuste_altura_grid_carteira,
    aplicar_estilo_grid_carteira,
    vincular_ajuste_altura_grid_carteira,
)
from src.View.tema import CORES

_COLUNAS = (
    "tipo",
    "ativo",
    "nome",
    "quantidade",
    "data_compra",
    "preco_compra",
    "valor_compra",
    "situacao",
)
_ROTULOS = {
    "tipo": "Tipo",
    "ativo": "Ativo",
    "nome": "Nome",
    "quantidade": "Qtd",
    "data_compra": "Data compra",
    "preco_compra": "Preco compra",
    "valor_compra": "Valor compra",
    "situacao": "Situacao",
}
_LARGURAS = (80, 75, 160, 65, 95, 100, 110, 110)


def _formatar_quantidade(valor: float) -> str:
    texto = f"{valor:.8f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def _texto_situacao(linha: LinhaCompraCarteira) -> str:
    return "Na carteira" if linha.na_carteira else "Fora da carteira"


def criar_grid_compras_carteira(
    pai: ctk.CTkBaseClass,
    titulo: str,
    *,
    altura: int = 6,
    modo_tela_cheia: bool = False,
    ao_duplo_clique=None,
) -> ttk.Treeview:
    """Monta a treeview de compras no mesmo padrao da grid de vendas."""
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
        text="Clique no titulo da coluna para filtrar e ordenar. Duplo clique abre a edicao da compra.",
        font=ctk.CTkFont(size=11),
        text_color=CORES["textoSecundario"],
    ).pack(anchor="w", padx=12, pady=(0, 8))

    frame_tabela = ctk.CTkFrame(card, fg_color="transparent")
    frame_tabela.pack(fill="both", expand=True, padx=12, pady=(0, 8))
    frame_tabela.grid_rowconfigure(0, weight=1)
    frame_tabela.grid_columnconfigure(0, weight=1)

    tabela = ttk.Treeview(
        frame_tabela,
        columns=_COLUNAS,
        show="headings",
        height=altura,
        selectmode="extended",
    )
    tabela._ordenacao_configurada = False  # type: ignore[attr-defined]
    tabela._coluna_ordenacao = "data_compra"  # type: ignore[attr-defined]
    tabela._ordenacao_desc = True  # type: ignore[attr-defined]
    tabela._linhas_originais: list[LinhaCompraCarteira] = []  # type: ignore[attr-defined]
    inicializar_filtros_coluna_treeview(tabela)

    scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela.yview)
    scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=tabela.xview)
    tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    frame_tabela.grid_rowconfigure(0, weight=1)
    frame_tabela.grid_columnconfigure(0, weight=1)
    tabela.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, columnspan=2, sticky="ew")

    for coluna, largura in zip(_COLUNAS, _LARGURAS, strict=True):
        tabela.column(
            coluna,
            width=largura,
            minwidth=largura,
            anchor="w",
            stretch=not modo_tela_cheia,
        )
        tabela.heading(
            coluna,
            text=_ROTULOS[coluna],
            command=lambda c=coluna: _abrir_filtro_coluna_compras(tabela, c),
        )

    atualizar_cabecalhos_com_filtro_treeview(
        tabela,
        _COLUNAS,
        _ROTULOS,
        lambda coluna: _abrir_filtro_coluna_compras(tabela, coluna),
    )

    aplicar_estilo_grid_carteira(tabela)
    configurar_interacao_treeview(tabela, ao_duplo_clique=ao_duplo_clique)

    label_vazio = ctk.CTkLabel(
        card,
        text="Nenhuma compra registrada. Use Registrar compra na carteira.",
        font=ctk.CTkFont(size=13),
        text_color=CORES["textoSecundario"],
    )
    label_vazio.pack(pady=(0, 12))
    label_vazio.pack_forget()

    tabela._card_pai = card  # type: ignore[attr-defined]
    tabela._label_vazio = label_vazio  # type: ignore[attr-defined]
    tabela._altura_minima = altura  # type: ignore[attr-defined]
    tabela._scroll_y = scroll_y  # type: ignore[attr-defined]
    tabela._scroll_x = scroll_x  # type: ignore[attr-defined]
    tabela._modo_tela_cheia = modo_tela_cheia  # type: ignore[attr-defined]
    vincular_botao_exportar_treeview(frame_botoes, tabela, titulo, janela_pai=card)
    vincular_ajuste_altura_grid_carteira(tabela)
    return tabela


def aplicar_ajuste_altura_grid_compras(tabela: ttk.Treeview | None) -> None:
    if tabela is None:
        return
    aplicar_ajuste_altura_grid_carteira(tabela)


def preencher_grid_compras_carteira(
    tabela: ttk.Treeview,
    linhas: list[LinhaCompraCarteira],
) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    tabela._linhas_originais = list(linhas)  # type: ignore[attr-defined]
    _renderizar_grid_compras_carteira(tabela)


def _renderizar_grid_compras_carteira(tabela: ttk.Treeview) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    linhas_originais = list(getattr(tabela, "_linhas_originais", []))
    linhas = aplicar_filtros_coluna_treeview(linhas_originais, tabela, _valor_celula_compra)
    coluna = getattr(tabela, "_coluna_ordenacao", "data_compra")
    descendente = getattr(tabela, "_ordenacao_desc", True)
    ordenadas = _ordenar_linhas_compras(linhas, coluna, descendente)
    atualizar_cabecalhos_com_filtro_treeview(
        tabela,
        _COLUNAS,
        _ROTULOS,
        lambda col: _abrir_filtro_coluna_compras(tabela, col),
    )

    liberar_interacao_treeview(tabela)
    tabela._tags_zebra = {}  # type: ignore[attr-defined]

    for item in tabela.get_children():
        tabela.delete(item)

    label_vazio = getattr(tabela, "_label_vazio", None)
    if not ordenadas:
        if label_vazio is not None:
            if linhas_originais:
                label_vazio.configure(
                    text="Nenhuma compra corresponde aos filtros atuais.",
                )
            else:
                label_vazio.configure(
                    text="Nenhuma compra registrada. Use Registrar compra na carteira.",
                )
            label_vazio.pack(pady=(0, 12))
    elif label_vazio is not None:
        label_vazio.pack_forget()

    for indice, linha in enumerate(ordenadas):
        compra = linha.compra
        moeda = linha.moeda
        tag = "normal_par" if indice % 2 == 0 else "normal_impar"
        tabela._tags_zebra[compra.id] = tag  # type: ignore[attr-defined]
        tabela.insert(
            "",
            "end",
            iid=compra.id,
            values=(
                ROTULOS_TIPO_CARTEIRA.get(compra.tipo_ativo, compra.tipo_ativo),
                codigo_exibicao(compra.simbolo),
                linha.nome,
                _formatar_quantidade(compra.quantidade),
                compra.data_compra,
                formatar_moeda(compra.preco_compra, moeda),
                formatar_moeda(compra.valor_compra, moeda),
                _texto_situacao(linha),
            ),
            tags=(tag,),
        )

    aplicar_ajuste_altura_grid_compras(tabela)
    sincronizar_tags_selecao_treeview(tabela)


def _valor_celula_compra(linha: LinhaCompraCarteira, coluna: str) -> str:
    compra = linha.compra
    moeda = linha.moeda
    if coluna == "tipo":
        return ROTULOS_TIPO_CARTEIRA.get(compra.tipo_ativo, compra.tipo_ativo)
    if coluna == "ativo":
        return codigo_exibicao(compra.simbolo)
    if coluna == "nome":
        return linha.nome
    if coluna == "quantidade":
        return _formatar_quantidade(compra.quantidade)
    if coluna == "data_compra":
        return compra.data_compra
    if coluna == "preco_compra":
        return formatar_moeda(compra.preco_compra, moeda)
    if coluna == "valor_compra":
        return formatar_moeda(compra.valor_compra, moeda)
    if coluna == "situacao":
        return _texto_situacao(linha)
    return ""


def _abrir_filtro_coluna_compras(tabela: ttk.Treeview, coluna: str) -> None:
    abrir_popup_filtro_coluna_treeview(
        tabela=tabela,
        coluna=coluna,
        rotulo_coluna=_ROTULOS.get(coluna, coluna),
        linhas=list(getattr(tabela, "_linhas_originais", [])),
        obter_valor=_valor_celula_compra,
        ao_atualizar=lambda: _renderizar_grid_compras_carteira(tabela),
        definir_ordenacao=lambda col, desc: _definir_ordenacao_compras(tabela, col, desc),
    )


def _definir_ordenacao_compras(tabela: ttk.Treeview, coluna: str, descendente: bool) -> None:
    tabela._coluna_ordenacao = coluna  # type: ignore[attr-defined]
    tabela._ordenacao_desc = descendente  # type: ignore[attr-defined]



def liberar_grid_compras_carteira(tabela: ttk.Treeview | None) -> None:
    if tabela is None:
        return
    liberar_interacao_treeview(tabela)


def obter_ids_selecionados_compras(tabela: ttk.Treeview | None) -> list[str]:
    if tabela is None or not treeview_ainda_ativa(tabela):
        return []
    return [str(item) for item in tabela.selection()]


def obter_linha_compra_por_id(
    tabela: ttk.Treeview | None,
    compra_id: str,
) -> LinhaCompraCarteira | None:
    if tabela is None:
        return None
    for linha in getattr(tabela, "_linhas_originais", []):
        if linha.compra.id == compra_id:
            return linha
    return None


def _chave_ordenacao_linha(linha: LinhaCompraCarteira, coluna: str) -> tuple:
    compra = linha.compra
    if coluna == "tipo":
        return chave_comparavel(ROTULOS_TIPO_CARTEIRA.get(compra.tipo_ativo, compra.tipo_ativo))
    if coluna == "ativo":
        return chave_comparavel(codigo_exibicao(compra.simbolo))
    if coluna == "nome":
        return chave_comparavel(linha.nome)
    if coluna == "quantidade":
        return chave_comparavel(compra.quantidade)
    if coluna == "data_compra":
        return chave_comparavel(compra.data_compra)
    if coluna == "preco_compra":
        return chave_comparavel(compra.preco_compra)
    if coluna == "valor_compra":
        return chave_comparavel(compra.valor_compra)
    if coluna == "situacao":
        return chave_comparavel(_texto_situacao(linha))
    return chave_comparavel("")


def _ordenar_linhas_compras(
    linhas: list[LinhaCompraCarteira],
    coluna: str | None,
    descendente: bool,
) -> list[LinhaCompraCarteira]:
    if not coluna or not linhas:
        return linhas
    return sorted(
        linhas,
        key=lambda linha: _chave_ordenacao_linha(linha, coluna),
        reverse=descendente,
    )
