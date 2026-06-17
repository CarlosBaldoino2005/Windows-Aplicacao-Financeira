"""Grid do historico de vendas da carteira com ordenacao por coluna."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk

from src.Model.carteira import ROTULOS_TIPO_CARTEIRA, LinhaVendaCarteira
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.View.formatadores import formatar_moeda
from src.View.grid_ordenacao_helper import SUFIXO_ASCENDENTE, SUFIXO_DESCENDENTE, chave_comparavel
from src.View.grid_interacao_treeview_helper import (
    configurar_interacao_treeview,
    liberar_interacao_treeview,
    treeview_ainda_ativa,
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
    "data_venda",
    "preco_venda",
    "valor_venda",
    "dividendos",
    "lucro_reais",
    "lucro_pct",
)
_ROTULOS = {
    "tipo": "Tipo",
    "ativo": "Ativo",
    "nome": "Nome",
    "quantidade": "Qtd",
    "data_compra": "Compra",
    "preco_compra": "Preco compra",
    "valor_compra": "Valor compra",
    "data_venda": "Venda",
    "preco_venda": "Preco venda",
    "valor_venda": "Valor venda",
    "dividendos": "Dividendos",
    "lucro_reais": "Lucro total",
    "lucro_pct": "Lucro %",
}
_LARGURAS = (80, 75, 140, 65, 85, 95, 100, 85, 95, 100, 95, 105, 80)


def _formatar_quantidade(valor: float) -> str:
    texto = f"{valor:.8f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def _formatar_lucro_pct(valor: float | None) -> str:
    if valor is None:
        return "—"
    sinal = "+" if valor >= 0 else ""
    return f"{sinal}{valor:.2f}%"


def criar_grid_vendas_carteira(
    pai: ctk.CTkBaseClass,
    titulo: str,
    *,
    altura: int = 6,
    modo_tela_cheia: bool = False,
) -> ttk.Treeview:
    """Monta a treeview de vendas no mesmo padrao da grid da carteira."""
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
        text="Clique no titulo da coluna para ordenar. Verde = lucro; vermelho = prejuizo.",
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
    tabela._coluna_ordenacao = "data_venda"  # type: ignore[attr-defined]
    tabela._ordenacao_desc = True  # type: ignore[attr-defined]
    tabela._linhas_originais: list[LinhaVendaCarteira] = []  # type: ignore[attr-defined]

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
            command=lambda c=coluna: _alternar_ordenacao_vendas(tabela, c),
        )

    aplicar_estilo_grid_carteira(tabela)
    configurar_interacao_treeview(tabela)

    label_vazio = ctk.CTkLabel(
        card,
        text="Nenhuma venda registrada. Use Registrar venda na carteira.",
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
    vincular_ajuste_altura_grid_carteira(tabela)
    return tabela


def aplicar_ajuste_altura_grid_vendas(tabela: ttk.Treeview | None) -> None:
    """Recalcula linhas visiveis da grid de vendas."""
    if tabela is None:
        return
    aplicar_ajuste_altura_grid_carteira(tabela)


def preencher_grid_vendas_carteira(
    tabela: ttk.Treeview,
    linhas: list[LinhaVendaCarteira],
) -> None:
    """Atualiza linhas da grid de vendas."""
    if not treeview_ainda_ativa(tabela):
        return

    tabela._linhas_originais = list(linhas)  # type: ignore[attr-defined]
    coluna = getattr(tabela, "_coluna_ordenacao", "data_venda")
    descendente = getattr(tabela, "_ordenacao_desc", True)
    ordenadas = _ordenar_linhas_vendas(linhas, coluna, descendente)
    _atualizar_cabecalhos_ordenacao(tabela)

    for item in tabela.get_children():
        tabela.delete(item)

    label_vazio = getattr(tabela, "_label_vazio", None)
    if not ordenadas:
        if label_vazio is not None:
            label_vazio.pack(pady=(0, 12))
    elif label_vazio is not None:
        label_vazio.pack_forget()

    for indice, linha in enumerate(ordenadas):
        venda = linha.venda
        moeda = linha.moeda
        tag = _tag_lucro(venda.lucro_total, indice)
        tabela.insert(
            "",
            "end",
            iid=venda.id,
            values=(
                ROTULOS_TIPO_CARTEIRA.get(venda.tipo_ativo, venda.tipo_ativo),
                codigo_exibicao(venda.simbolo),
                linha.nome,
                _formatar_quantidade(venda.quantidade),
                venda.data_compra,
                formatar_moeda(venda.preco_compra, moeda),
                formatar_moeda(venda.valor_compra, moeda),
                venda.data_venda,
                formatar_moeda(venda.preco_venda, moeda),
                formatar_moeda(venda.valor_venda, moeda),
                formatar_moeda(venda.dividendos_recebidos, moeda),
                formatar_moeda(venda.lucro_total, moeda),
                _formatar_lucro_pct(venda.lucro_percentual),
            ),
            tags=(tag,),
        )

    aplicar_ajuste_altura_grid_vendas(tabela)


def liberar_grid_vendas_carteira(tabela: ttk.Treeview | None) -> None:
    if tabela is None:
        return
    liberar_interacao_treeview(tabela)


def _alternar_ordenacao_vendas(tabela: ttk.Treeview, coluna: str) -> None:
    if getattr(tabela, "_coluna_ordenacao", None) == coluna:
        tabela._ordenacao_desc = not getattr(tabela, "_ordenacao_desc", False)  # type: ignore[attr-defined]
    else:
        tabela._coluna_ordenacao = coluna  # type: ignore[attr-defined]
        tabela._ordenacao_desc = False  # type: ignore[attr-defined]
    linhas = list(getattr(tabela, "_linhas_originais", []))
    preencher_grid_vendas_carteira(tabela, linhas)


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
            command=lambda c=coluna: _alternar_ordenacao_vendas(tabela, c),
        )


def _chave_ordenacao_linha(linha: LinhaVendaCarteira, coluna: str) -> tuple:
    venda = linha.venda
    if coluna == "tipo":
        return chave_comparavel(ROTULOS_TIPO_CARTEIRA.get(venda.tipo_ativo, venda.tipo_ativo))
    if coluna == "ativo":
        return chave_comparavel(codigo_exibicao(venda.simbolo))
    if coluna == "nome":
        return chave_comparavel(linha.nome)
    if coluna == "quantidade":
        return chave_comparavel(venda.quantidade)
    if coluna == "data_compra":
        return chave_comparavel(venda.data_compra)
    if coluna == "preco_compra":
        return chave_comparavel(venda.preco_compra)
    if coluna == "valor_compra":
        return chave_comparavel(venda.valor_compra)
    if coluna == "data_venda":
        return chave_comparavel(venda.data_venda)
    if coluna == "preco_venda":
        return chave_comparavel(venda.preco_venda)
    if coluna == "valor_venda":
        return chave_comparavel(venda.valor_venda)
    if coluna == "dividendos":
        return chave_comparavel(venda.dividendos_recebidos)
    if coluna == "lucro_reais":
        return chave_comparavel(venda.lucro_total)
    if coluna == "lucro_pct":
        return chave_comparavel(venda.lucro_percentual)
    return chave_comparavel("")


def _ordenar_linhas_vendas(
    linhas: list[LinhaVendaCarteira],
    coluna: str | None,
    descendente: bool,
) -> list[LinhaVendaCarteira]:
    if not coluna or not linhas:
        return linhas
    return sorted(
        linhas,
        key=lambda linha: _chave_ordenacao_linha(linha, coluna),
        reverse=descendente,
    )


def _tag_lucro(lucro: float, indice: int) -> str:
    if lucro > 0:
        return "positivo"
    if lucro < 0:
        return "negativo"
    return "normal_par" if indice % 2 == 0 else "normal_impar"
