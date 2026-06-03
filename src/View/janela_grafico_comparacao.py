"""Janela dedicada para visualizar o grafico de comparacao entre acoes."""
import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Service.cdi_servico import CdiServico
from src.Tool.janela_helper import configurar_janela_maximizada
from src.View.grafico_helper import COR_LINHA_CDI
from src.View.grafico_helper import (
    TEXTO_INSTRUCAO_GRAFICO_COMPARACAO,
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
        self._desenhando_grafico = False

        self._montar_interface()
        configurar_janela_maximizada(self, ao_apos_layout=self._desenhar_grafico)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

    def _montar_interface(self) -> None:
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["secundaria"],
            width=120,
        ).pack(side="right")

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(side="top", fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Comparacao de acoes (indice base 100 no 1º dia)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Passe o mouse para detalhes. Linha laranja tracejada: 100% CDI (indice base 100). "
                "Clique em 2 pontos para comparar o intervalo (marcadores vermelhos)."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self._frame_painel_resultado = ctk.CTkScrollableFrame(
            cabecalho,
            height=200,
            fg_color=CORES["fundo"],
            label_text="Resumo da comparacao por periodo",
        )
        self._frame_painel_resultado.pack(fill="x", padx=16, pady=(0, 12))
        texto_painel = TEXTO_INSTRUCAO_GRAFICO_COMPARACAO
        avisos = self._dados.get("avisos") or []
        if avisos:
            texto_painel += " Avisos: " + " | ".join(avisos)
        PainelComparacaoPeriodo.exibir(
            self._frame_painel_resultado,
            payload_instrucao(texto_painel),
        )

        self._frame_grafico = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._frame_grafico.pack(side="top", fill="both", expand=True, padx=16, pady=(8, 8))

    def _atualizar_painel_comparacao(self, payload: dict) -> None:
        PainelComparacaoPeriodo.exibir(self._frame_painel_resultado, payload)

    def _area_grafico_valida(self) -> bool:
        try:
            return self._frame_grafico.winfo_width() > 80 and self._frame_grafico.winfo_height() > 80
        except Exception:
            return False

    def _desenhar_grafico(self, tentativa: int = 0) -> None:
        if self._desenhando_grafico and tentativa == 0:
            self.after(100, lambda: self._desenhar_grafico(0))
            return

        if not self._area_grafico_valida():
            if tentativa < 40:
                self.after(80, lambda: self._desenhar_grafico(tentativa + 1))
            return

        self._desenhando_grafico = True
        try:
            self._montar_figura_comparacao()
        finally:
            self._desenhando_grafico = False

    def _montar_figura_comparacao(self) -> None:
        for widget in self._frame_grafico.winfo_children():
            widget.destroy()

        if self._figura:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None

        dados = self._dados
        simbolos = dados.get("simbolos") or []
        if not simbolos:
            return

        serie_referencia = dados["series"].get(simbolos[0]) or []
        if not serie_referencia:
            return

        largura_px = max(400, self._frame_grafico.winfo_width() - 16)
        altura_px = max(300, self._frame_grafico.winfo_height() - 16)
        dpi = 100
        figura = Figure(
            figsize=(largura_px / dpi, altura_px / dpi),
            dpi=dpi,
            facecolor=CORES.get("graficoFundo", CORES["superficie"]),
        )
        eixo = figura.add_subplot(111)
        linhas_plot: list = []

        indices = np.arange(len(serie_referencia))
        datas_grafico = [p["data"] for p in serie_referencia]

        for i, simbolo in enumerate(simbolos):
            serie = dados["series"].get(simbolo) or []
            if len(serie) < 2:
                continue
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

        try:
            valores_cdi = CdiServico().montar_indice_cdi_base100(datas_grafico)
            if valores_cdi and len(valores_cdi) == len(serie_referencia):
                eixo.plot(
                    indices,
                    valores_cdi,
                    label="100% CDI",
                    color=COR_LINHA_CDI,
                    linewidth=2.5,
                    linestyle="--",
                    marker="s",
                    markersize=4,
                )
        except Exception:
            pass

        eixo.set_xticks(indices)
        eixo.set_xticklabels(datas_grafico, rotation=30, ha="right", fontsize=9)
        eixo.set_title("Desempenho relativo no periodo", fontsize=14, fontweight="bold")
        eixo.set_ylabel("Indice relativo (base 100)", fontsize=11)
        eixo.legend(loc="best", fontsize=10)
        eixo.grid(True, alpha=0.3)
        figura.subplots_adjust(bottom=0.2, left=0.08, right=0.96, top=0.92)

        self._figura = figura
        self._canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        if linhas_plot:
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

    def _ao_fechar(self) -> None:
        if self._figura:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
        self.destroy()
