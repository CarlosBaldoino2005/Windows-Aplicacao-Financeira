"""Abre a tela Agora a partir da selecao em grids de hub de mercado."""
from __future__ import annotations

from typing import Any

import customtkinter as ctk
from tkinter import ttk

from src.View import mensagem_helper as messagebox
from src.View.grid_interacao_treeview_helper import (
    obter_simbolo_unico_selecionado_treeview,
    treeview_ainda_ativa,
)
from src.View.janela_grafico_tempo_real import JanelaGraficoTempoReal, abrir_grafico_tempo_real


def obter_tabela_aba_ativa(
    nome_aba: str,
    tabelas_por_aba: dict[str, ttk.Treeview],
    *,
    padrao: str | None = None,
) -> ttk.Treeview | None:
    """Retorna a grid da aba visivel no hub."""
    if nome_aba in tabelas_por_aba:
        return tabelas_por_aba[nome_aba]
    if padrao and padrao in tabelas_por_aba:
        return tabelas_por_aba[padrao]
    for tabela in tabelas_por_aba.values():
        if treeview_ainda_ativa(tabela):
            return tabela
    return None


def abrir_agora_da_selecao_grid(
    pai: ctk.CTkToplevel,
    controlador: Any,
    tabela: ttk.Treeview | None,
    janela_agora_atual: JanelaGraficoTempoReal | None = None,
) -> JanelaGraficoTempoReal | None:
    """Abre ou foca a tela Agora para o unico ativo selecionado na grid."""
    simbolo = obter_simbolo_unico_selecionado_treeview(tabela)
    if not simbolo:
        messagebox.showwarning(
            "Agora",
            "Selecione exatamente um ativo na grid para acompanhar em tempo real.",
            parent=pai,
        )
        return janela_agora_atual

    if janela_agora_atual is not None:
        try:
            if janela_agora_atual.winfo_exists():
                if getattr(janela_agora_atual, "_simbolo", None) == simbolo:
                    janela_agora_atual.focus_force()
                    janela_agora_atual.lift()
                    return janela_agora_atual
                janela_agora_atual._ao_fechar()
        except Exception:
            pass

    return abrir_grafico_tempo_real(pai, controlador, simbolo)
