"""Janela dedicada para visualizar o grafico de comparacao entre acoes."""
import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Tool.janela_helper import maximizar_janela
from src.View.grafico_helper import (
    configurar_selecao_periodo_comparacao,
    configurar_tooltip_comparacao,
)
from src.View.painel_comparacao_periodo import PainelComparacaoPeriodo, payload_instrucao
from src.View.tema import CORES

CORES_GRAFICO = ["#2563EB", "#16A34A", "#D97706", "#DC2626", "#7C3AED", "#0891B2"]


class JanelaGraficoComparacao(ctk.CTkToplevel):
    """Tela ampla com grafico, tooltip e selecao vermelha por periodo."""

    def __init__(self, pai: ctk.CTk, dados: dict, rotulo_periodo: str) -> None:
        super().__init__(pai)
        self._dados = dados
        simbolos_txt = ", ".join(s.replace(".SA", "") for s in dados["simbolos"])
        self.title(f"Comparacao de acoes — {rotulo_periodo} — {simbolos_txt}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 600)

        self._figura = None
        self._canvas = None

        self._montar_interface()
        self.after(0, lambda: maximizar_janela(self))
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Comparacao de acoes (indice base 100 no 1º dia)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text="Passe o mouse para detalhes. Clique em 2 pontos para comparar o intervalo (marcadores vermelhos).",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self._frame_painel_resultado = ctk.CTkScrollableFrame(
            cabecalho,
            height=220,
            fg_color=CORES["fundo"],
            label_text="Resumo da comparacao por periodo",
        )
        self._frame_painel_resultado.pack(fill="x", padx=16, pady=(0, 12))
        PainelComparacaoPeriodo.exibir(
            self._frame_painel_resultado,
            payload_instrucao(
                "Clique no grafico: 1º ponto (inicio) e 2º ponto (fim) para comparar o periodo entre as acoes."
            ),
        )

        self._frame_grafico = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._frame_grafico.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["secundaria"],
            width=120,
        ).pack(side="right")

        self._desenhar_grafico()

    def _atualizar_painel_comparacao(self, payload: dict) -> None:
        PainelComparacaoPeriodo.exibir(self._frame_painel_resultado, payload)

    def _desenhar_grafico(self) -> None:
        for widget in self._frame_grafico.winfo_children():
            widget.destroy()

        dados = self._dados
        simbolos = dados["simbolos"]

        figura = Figure(figsize=(12, 7), dpi=100, facecolor=CORES["superficie"])
        eixo = figura.add_subplot(111)
        linhas_plot: list = []

        for i, simbolo in enumerate(simbolos):
            serie = dados["series"][simbolo]
            indices = np.arange(len(serie))
            linha, = eixo.plot(
                indices,
                [p["indice_relativo"] for p in serie],
                label=simbolo.replace(".SA", ""),
                color=CORES_GRAFICO[i % len(CORES_GRAFICO)],
                linewidth=2.5,
                marker="o",
                markersize=4,
            )
            linhas_plot.append(linha)
            if i == 0:
                eixo.set_xticks(indices)
                eixo.set_xticklabels([p["data"] for p in serie], rotation=30, ha="right", fontsize=9)

        eixo.set_title("Desempenho relativo no periodo", fontsize=14, fontweight="bold")
        eixo.set_ylabel("Indice relativo (base 100)", fontsize=11)
        eixo.legend(loc="best", fontsize=10)
        eixo.grid(True, alpha=0.3)
        figura.subplots_adjust(bottom=0.2, left=0.08, right=0.96, top=0.92)

        self._figura = figura
        self._canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)
        configurar_tooltip_comparacao(
            self._canvas, eixo, linhas_plot, dados["series"], simbolos
        )
        configurar_selecao_periodo_comparacao(
            self._canvas,
            eixo,
            linhas_plot,
            dados["series"],
            simbolos,
            self._atualizar_painel_comparacao,
        )
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _ao_fechar(self) -> None:
        if self._figura:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
        self.destroy()
