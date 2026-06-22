"""Janela dedicada ao grafico comparativo da carteira."""
from __future__ import annotations

import customtkinter as ctk

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import LinhaCarteira
from src.Tool.janela_helper import (
    ajustar_janela_area_trabalho,
    configurar_janela_maximizada,
    janela_ui_ainda_ativa,
)
from src.View.painel_grafico_carteira_helper import PainelGraficoCarteira
from src.View.tema import CORES


class JanelaGraficoCarteira(ctk.CTkToplevel):
    """Comparacao dos ativos da carteira (indice base 100) em tela propria."""

    def __init__(
        self,
        pai: ctk.CTk | ctk.CTkToplevel,
        controlador: ControladorCarteira,
        linhas: list[LinhaCarteira] | None = None,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._linhas = list(linhas or [])

        self.title("Carteira — grafico comparativo")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(960, 640)

        self._montar_interface()
        configurar_janela_maximizada(
            self,
            janela_pai=pai,
            ao_apos_layout=self._ajustar_layout,
        )
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

        if self._linhas:
            self.after(250, lambda: self._painel.atualizar_linhas(self._linhas))
        self.after(500, self._ajustar_layout)

    def _montar_interface(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        conteudo = ctk.CTkFrame(self, fg_color=CORES["fundo"])
        conteudo.grid(row=0, column=0, sticky="nsew")
        conteudo.grid_rowconfigure(0, weight=1)
        conteudo.grid_columnconfigure(0, weight=1)

        self._painel = PainelGraficoCarteira(self, self._controlador, modo_janela=True)
        card = self._painel.montar(conteudo)
        card.pack(fill="both", expand=True, padx=16, pady=16)

    def _ajustar_layout(self) -> None:
        if not janela_ui_ainda_ativa(self):
            return
        ajustar_janela_area_trabalho(self)
        self._painel.reaplicar_layout()

    def atualizar_linhas(self, linhas: list[LinhaCarteira]) -> None:
        self._linhas = list(linhas)
        self._painel.atualizar_linhas(linhas)

    def _ao_fechar(self) -> None:
        self._painel.liberar()
        self.destroy()


def abrir_grafico_carteira(
    pai: ctk.CTk | ctk.CTkToplevel,
    controlador: ControladorCarteira,
    linhas: list[LinhaCarteira],
) -> JanelaGraficoCarteira | None:
    if not pai.winfo_exists():
        return None
    return JanelaGraficoCarteira(pai, controlador, linhas)
