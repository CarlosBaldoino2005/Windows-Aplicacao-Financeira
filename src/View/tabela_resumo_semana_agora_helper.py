"""Grid do resumo mensal da tela Agora."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk

from src.Model.opcoes_fonte_grid import OpcoesFonteGrid
from src.Model.resumo_semana_agora import DiaResumoSemanaAgora, ResumoSemanaAgora
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.dia_util_helper import formatar_data_ptbr
from src.Tool.horario_extremo_intraday_helper import horario_para_minutos_ordenacao
from src.View.exportar_xlsx_grid_helper import (
    criar_frame_botoes_titulo_grid,
    vincular_botao_exportar_treeview,
)
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.grid_interacao_treeview_helper import (
    aplicar_destaque_estilo_treeview,
    aplicar_destaque_tags_treeview,
    configurar_interacao_treeview,
    liberar_interacao_treeview,
    sincronizar_tags_selecao_treeview,
    treeview_ainda_ativa,
)
from src.View.grid_ordenacao_helper import SUFIXO_ASCENDENTE, SUFIXO_DESCENDENTE, chave_comparavel
from src.View.tema import CORES

_COLUNAS = (
    "data",
    "abertura",
    "baixa",
    "hora_baixa",
    "alta",
    "hora_alta",
    "fechamento",
    "variacao",
    "amplitude",
    "volume",
)
_ROTULOS = {
    "data": "Data",
    "abertura": "Abertura",
    "baixa": "Baixa",
    "hora_baixa": "Hora baixa",
    "alta": "Alta",
    "hora_alta": "Hora alta",
    "fechamento": "Fechamento",
    "variacao": "Variacao",
    "amplitude": "Var. alta-baixa",
    "volume": "Volume",
}
_LARGURAS = {
    "data": 96,
    "abertura": 100,
    "baixa": 100,
    "hora_baixa": 80,
    "alta": 100,
    "hora_alta": 80,
    "fechamento": 108,
    "variacao": 168,
    "amplitude": 168,
    "volume": 118,
}
_ANCORAS = {
    "data": "center",
    "abertura": "e",
    "baixa": "e",
    "hora_baixa": "center",
    "alta": "e",
    "hora_alta": "center",
    "fechamento": "e",
    "variacao": "e",
    "amplitude": "e",
    "volume": "e",
}
_FONTE_FAMILIA = "Segoe UI"


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
            command=lambda c=coluna: alternar_ordenacao_resumo_semana(tabela, c),
        )


def _configurar_ordenacao_colunas(tabela: ttk.Treeview) -> None:
    tabela._coluna_ordenacao = "data"  # type: ignore[attr-defined]
    tabela._ordenacao_desc = True  # type: ignore[attr-defined]
    _atualizar_cabecalhos_ordenacao(tabela)


def alternar_ordenacao_resumo_semana(tabela: ttk.Treeview, coluna: str) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    if getattr(tabela, "_coluna_ordenacao", None) == coluna:
        tabela._ordenacao_desc = not getattr(tabela, "_ordenacao_desc", False)  # type: ignore[attr-defined]
    else:
        tabela._coluna_ordenacao = coluna  # type: ignore[attr-defined]
        tabela._ordenacao_desc = coluna != "data"

    _atualizar_cabecalhos_ordenacao(tabela)
    resumo = getattr(tabela, "_resumo_semana", None)
    if resumo is not None:
        preencher_grid_resumo_semana_agora(tabela, resumo)


def _ordenar_dias(tabela: ttk.Treeview, dias: list[DiaResumoSemanaAgora]) -> list[DiaResumoSemanaAgora]:
    coluna = getattr(tabela, "_coluna_ordenacao", "data")
    descendente = getattr(tabela, "_ordenacao_desc", True)
    moeda = getattr(tabela, "_moeda_resumo", "BRL")

    def chave(dia: DiaResumoSemanaAgora):
        mapa = {
            "data": dia.data.toordinal(),
            "abertura": dia.abertura,
            "baixa": dia.minima,
            "hora_baixa": horario_para_minutos_ordenacao(dia.horario_baixa),
            "alta": dia.maxima,
            "hora_alta": horario_para_minutos_ordenacao(dia.horario_alta),
            "fechamento": dia.fechamento,
            "variacao": dia.variacao_pct,
            "amplitude": dia.amplitude_pct,
            "volume": dia.volume if dia.volume is not None else -1,
        }
        valor = mapa.get(coluna, dia.data.toordinal())
        if coluna == "data":
            return valor
        return chave_comparavel(valor, moeda=moeda)

    return sorted(dias, key=chave, reverse=descendente)


def _tag_linha(indice: int, dia: DiaResumoSemanaAgora) -> str:
    zebra = "par" if indice % 2 == 0 else "impar"
    variacao = "var_pos" if dia.variacao_valor >= 0 else "var_neg"
    return f"{zebra}_{variacao}"


def aplicar_estilo_grid_resumo_semana_agora(
    tabela: ttk.Treeview,
    opcoes: OpcoesFonteGrid | None = None,
) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    opcoes_grid = _resolver_opcoes(opcoes)
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure(
        "ResumoSemana.Treeview",
        font=(_FONTE_FAMILIA, opcoes_grid.fonte_tree),
        rowheight=opcoes_grid.altura_linha,
        background=CORES["zebraClara"],
        fieldbackground=CORES["zebraClara"],
        foreground=CORES["texto"],
        borderwidth=0,
    )
    estilo.configure(
        "ResumoSemana.Treeview.Heading",
        font=(_FONTE_FAMILIA, opcoes_grid.fonte_cabecalho_tree, "bold"),
        background=CORES["zebraEscura"],
        foreground=CORES["texto"],
        relief="flat",
    )
    estilo.layout("ResumoSemana.Treeview", estilo.layout("Treeview"))
    tabela.configure(style="ResumoSemana.Treeview")
    aplicar_destaque_estilo_treeview(estilo)

    for zebra, fundo in (("par", CORES["zebraClara"]), ("impar", CORES["zebraEscura"])):
        tabela.tag_configure(
            f"{zebra}_var_pos",
            background=fundo,
            foreground=CORES["sucesso"],
        )
        tabela.tag_configure(
            f"{zebra}_var_neg",
            background=fundo,
            foreground=CORES["erro"],
        )

    aplicar_destaque_tags_treeview(tabela)


def criar_grid_resumo_semana_agora(
    pai: ctk.CTkFrame,
    titulo: str = "Ultimos 30 dias uteis",
    *,
    altura: int = 8,
    opcoes: OpcoesFonteGrid | None = None,
) -> ttk.Treeview:
    opcoes_grid = _resolver_opcoes(opcoes)

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

    frame_tabela = ctk.CTkFrame(card, fg_color="transparent")
    frame_tabela.pack(fill="both", expand=True, padx=12, pady=(0, 12))
    frame_tabela.grid_columnconfigure(0, weight=1)
    frame_tabela.grid_rowconfigure(0, weight=1)

    tabela = ttk.Treeview(
        frame_tabela,
        columns=_COLUNAS,
        show="headings",
        height=altura,
        selectmode="browse",
    )

    scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela.yview)
    scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=tabela.xview)
    tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    tabela.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")

    for coluna in _COLUNAS:
        largura = _LARGURAS[coluna]
        tabela.column(
            coluna,
            width=largura,
            minwidth=largura,
            stretch=False,
            anchor=_ANCORAS[coluna],
        )

    _configurar_ordenacao_colunas(tabela)
    aplicar_estilo_grid_resumo_semana_agora(tabela, opcoes_grid)
    configurar_interacao_treeview(tabela)

    vincular_botao_exportar_treeview(
        frame_botoes,
        tabela,
        "resumo_mes_agora",
        janela_pai=card,
    )
    return tabela


def preencher_grid_resumo_semana_agora(tabela: ttk.Treeview, resumo: ResumoSemanaAgora) -> None:
    if not treeview_ainda_ativa(tabela):
        return

    tabela._resumo_semana = resumo  # type: ignore[attr-defined]
    tabela._moeda_resumo = resumo.moeda  # type: ignore[attr-defined]

    liberar_interacao_treeview(tabela)
    tabela._tags_zebra = {}  # type: ignore[attr-defined]

    for item in tabela.get_children():
        tabela.delete(item)

    moeda = resumo.moeda
    dias = _ordenar_dias(tabela, list(resumo.dias))

    aplicar_estilo_grid_resumo_semana_agora(tabela)

    for indice, dia in enumerate(dias):
        tag = _tag_linha(indice, dia)
        iid = dia.data.isoformat()
        tabela._tags_zebra[iid] = tag  # type: ignore[attr-defined]
        volume_texto = f"{dia.volume:,}".replace(",", ".") if dia.volume is not None else "—"
        tabela.insert(
            "",
            "end",
            iid=iid,
            values=(
                formatar_data_ptbr(dia.data),
                formatar_moeda(dia.abertura, moeda),
                formatar_moeda(dia.minima, moeda),
                dia.horario_baixa,
                formatar_moeda(dia.maxima, moeda),
                dia.horario_alta,
                formatar_moeda(dia.fechamento, moeda),
                formatar_variacao(dia.variacao_valor, dia.variacao_pct, moeda),
                formatar_variacao(dia.amplitude_valor, dia.amplitude_pct, moeda),
                volume_texto,
            ),
            tags=(tag,),
        )

    sincronizar_tags_selecao_treeview(tabela)


def liberar_grid_resumo_semana_agora(tabela: ttk.Treeview | None) -> None:
    if tabela is None:
        return
    liberar_interacao_treeview(tabela)
