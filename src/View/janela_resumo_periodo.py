"""Janela ampliada para exibir o resumo do periodo com mais espaco."""
from __future__ import annotations

import customtkinter as ctk

from src.Tool.janela_helper import configurar_janela_maximizada
from src.View.painel_comparacao_periodo import PainelComparacaoPeriodo
from src.View.tema import CORES


class JanelaResumoPeriodo(ctk.CTkToplevel):
    """Mostra o mesmo resumo do grafico em tela maior, sem remover o painel compacto."""

    def __init__(self, pai: ctk.CTk, dados: dict, titulo: str) -> None:
        super().__init__(pai)
        self._dados = dados

        self.title(titulo)
        self.configure(fg_color=CORES["fundo"])
        self.minsize(820, 560)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Resumo ampliado do periodo",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Mesmos dados exibidos no painel compacto do grafico, "
                "com fontes maiores para leitura confortavel."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=CORES["superficie"],
            corner_radius=12,
            label_text="Detalhes do periodo",
        )
        scroll.pack(fill="both", expand=True, padx=16, pady=(8, 8))
        PainelComparacaoPeriodo.exibir(scroll, self._dados, modo_amplo=True)

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self.destroy,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")


def abrir_janela_resumo_periodo(
    pai: ctk.CTk, dados: dict, titulo: str
) -> JanelaResumoPeriodo | None:
    """Abre a janela ampliada quando houver resumo valido para exibir."""
    tipo = dados.get("tipo", "instrucao")
    if tipo not in ("completo", "parcial"):
        return None
    return JanelaResumoPeriodo(pai, dados, titulo)


def atualizar_estado_botao_resumo_ampliado(botao: ctk.CTkButton, dados: dict) -> None:
    """Habilita o botao apenas quando existir resumo util (parcial ou completo)."""
    tipo = dados.get("tipo", "instrucao")
    if tipo in ("completo", "parcial"):
        botao.configure(state="normal")
    else:
        botao.configure(state="disabled")
