"""Relatorio de IPOs dos ultimos 30 dias (Brasil e mundo)."""
from __future__ import annotations

from datetime import datetime

import customtkinter as ctk
from tkinter import ttk

from src.View import mensagem_helper as messagebox

from src.Controller.controlador_relatorios import ControladorRelatorios
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import (
    configurar_janela_maximizada,
    executar_em_thread,
    janela_ui_ainda_ativa,
)
from src.View.hub_painel_config_helper import ConfiguracaoHubPainel
from src.View.tabela_ipos_helper import (
    criar_tabela_ipos,
    preencher_tabela_ipos,
    reaplicar_fonte_tabela_ipos,
)
from src.View.tema import CORES


class PainelRelatorioIpos(ctk.CTkFrame):
    """Grade de IPOs reutilizavel no hub ou em janela dedicada."""

    def __init__(self, pai: ctk.CTkFrame, controlador: ControladorRelatorios) -> None:
        super().__init__(pai, fg_color=CORES["fundo"])
        self._controlador = controlador
        self._tabela: ttk.Treeview | None = None
        self._buscando = False

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 6))

        self._label_status = ctk.CTkLabel(
            barra,
            text="Carregando IPOs...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(side="left")

        ctk.CTkButton(
            barra,
            text="Atualizar",
            command=lambda: self.atualizar_grid(forcar=True),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._tabela = criar_tabela_ipos(
            container,
            "IPOs recentes (Brasil e mundo)",
            altura=22,
            expandir=True,
        )

    def ao_mudar_fonte_grid(self) -> None:
        reaplicar_fonte_tabela_ipos(self._tabela)

    def atualizar_grid(self, *, forcar: bool = False) -> None:
        janela = self.winfo_toplevel()
        if not janela_ui_ainda_ativa(janela):
            return
        if self._buscando and not forcar:
            return
        if self._tabela is None:
            return

        self._buscando = True
        self._label_status.configure(
            text="Buscando IPOs e cotacoes do dia...",
            text_color=CORES["textoSecundario"],
        )

        def buscar():
            return self._controlador.listar_ipos_ultimos_30_dias()

        def ao_concluir(resultado, erro_thread):
            self._buscando = False
            if not janela_ui_ainda_ativa(janela) or self._tabela is None:
                return

            if erro_thread:
                self._label_status.configure(text=erro_thread, text_color=CORES["erro"])
                messagebox.showerror("IPOs", erro_thread, parent=janela)
                return

            itens, msg_erro = resultado if resultado is not None else ([], "Falha na consulta.")
            if msg_erro and not itens:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                preencher_tabela_ipos(self._tabela, [], msg_erro)
                return

            preencher_tabela_ipos(
                self._tabela,
                itens,
                "Nenhum IPO encontrado nos ultimos 30 dias.",
            )
            hora = datetime.now().strftime("%H:%M:%S")
            self._label_status.configure(
                text=f"Atualizado as {hora} — {len(itens)} IPO(s) listado(s)",
                text_color=CORES["sucesso"],
            )

        executar_em_thread(janela, buscar, ao_concluir)


class JanelaRelatorioIpos(ctk.CTkToplevel):
    """Janela dedicada com grid de IPOs recentes (atalho fora do hub)."""

    def __init__(self, pai: ctk.CTk, controlador: ControladorRelatorios) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._config_painel = ConfigPainelIni()
        self._painel_ipos: PainelRelatorioIpos | None = None
        self._config_hub = ConfiguracaoHubPainel(
            self,
            self._config_painel,
            incluir_quantidade=False,
            ao_mudar_fonte=self._ao_mudar_fonte_grid,
            ao_remontar_layout=self._reconstruir_interface_apos_tema,
        )

        self.title("IPOs — ultimos 30 dias")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(1100, 640)

        self._montar_layout()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(250, lambda: self._atualizar_grid(forcar=False))

    def _ao_fechar(self) -> None:
        self.destroy()

    def _montar_layout(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        self._config_hub.montar_titulo_com_engrenagem(
            cabecalho,
            "IPOs — ultimos 30 dias",
        )

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Empresas que abriram capital nos ultimos 30 dias (B3 e mercados internacionais). "
                "Ordenado por data do IPO. Clique no cabecalho para ordenar ou filtrar."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        secao = ctk.CTkFrame(self, fg_color=CORES["fundo"])
        secao.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._painel_ipos = PainelRelatorioIpos(secao, self._controlador)
        self._painel_ipos.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self,
            text="Dados publicos (CVM, StockAnalysis, Yahoo Finance). Uso educacional.",
            font=ctk.CTkFont(size=11),
            text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
            fg_color=CORES.get("destaqueAvisoLegal", CORES["avisoFundo"]),
            corner_radius=8,
        ).pack(fill="x", padx=16, pady=(0, 12))

    def _reconstruir_interface_apos_tema(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()
        self._config_hub.limpar_referencia_modal()
        self.configure(fg_color=CORES["fundo"])
        self._montar_layout()
        self.after(250, lambda: self._atualizar_grid(forcar=True))

    def _ao_mudar_fonte_grid(self) -> None:
        if self._painel_ipos is not None:
            self._painel_ipos.ao_mudar_fonte_grid()

    def _atualizar_grid(self, *, forcar: bool = False) -> None:
        if self._painel_ipos is not None:
            self._painel_ipos.atualizar_grid(forcar=forcar)
