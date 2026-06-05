"""Janela ampliada exibindo somente o grafico em tela maior."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Service.cdi_servico import CdiServico
from src.Tool.janela_helper import configurar_janela_maximizada
from src.View.grafico_helper import (
    COR_LINHA_CDI,
    _publicar_payload_com_cdi,
    aplicar_tema_matplotlib,
    configurar_selecao_periodo,
    configurar_selecao_periodo_comparacao,
    configurar_tooltip_acao,
    configurar_tooltip_comparacao,
)
from src.View.painel_comparacao_periodo import calcular_comparacao_acao_unica
from src.View.tema import CORES

_CORES_GRAFICO = ["#2563EB", "#16A34A", "#D97706", "#DC2626", "#7C3AED", "#0891B2"]


class JanelaGraficoAmpliadoAcao(ctk.CTkToplevel):
    """Exibe o grafico de uma acao em tela maior, mantendo o grafico compacto na janela pai."""

    def __init__(
        self,
        pai: ctk.CTk,
        titulo_janela: str,
        dados_grafico: dict,
        obter_quantidade_cotas: Callable[[], int],
        atualizar_painel_pai: Callable[[dict], None],
    ) -> None:
        super().__init__(pai)
        self._dados_grafico = dados_grafico
        self._obter_quantidade_cotas = obter_quantidade_cotas
        self._atualizar_painel_pai = atualizar_painel_pai
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None

        self.title(titulo_janela)
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 620)

        self._montar_interface()
        configurar_janela_maximizada(self, ao_apos_layout=self._ajustar_grafico, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(120, self._ajustar_grafico)

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text=self._dados_grafico.get("titulo", "Grafico ampliado"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Visualizacao ampliada do grafico. Passe o mouse para detalhes "
                "e clique em dois pontos para comparar intervalos (o resumo atualiza na tela principal)."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=960,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 10))

        self._frame_grafico = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._frame_grafico.pack(fill="both", expand=True, padx=16, pady=(8, 8))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=120,
        ).pack(side="right")

        self._desenhar_grafico()

    def _desenhar_grafico(self) -> None:
        for widget in self._frame_grafico.winfo_children():
            widget.destroy()

        if self._figura is not None:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
            self._canvas = None

        dados = self._dados_grafico
        labels = dados["labels"]
        valores = dados["valores"]
        titulo = dados.get("titulo", "")
        simbolo = dados["simbolo"]
        moeda = dados["moeda"]
        pontos_tooltip = dados["pontos_tooltip"]
        valores_cdi = dados.get("valores_cdi")

        self._frame_grafico.update_idletasks()
        largura_px = max(600, self._frame_grafico.winfo_width() - 16)
        altura_px = max(450, self._frame_grafico.winfo_height() - 16)
        dpi = 100
        figura = Figure(
            figsize=(largura_px / dpi, altura_px / dpi),
            dpi=dpi,
            facecolor=CORES.get("graficoFundo", CORES["superficie"]),
        )
        eixo = figura.add_subplot(111)

        indices = np.arange(len(valores))
        linha, = eixo.plot(
            indices,
            valores,
            color=CORES["primaria"],
            linewidth=2.5,
            marker="o",
            markersize=4,
            label="Acao (fechamento)",
        )
        if valores_cdi and len(valores_cdi) == len(valores):
            eixo.plot(
                indices,
                valores_cdi,
                color=COR_LINHA_CDI,
                linewidth=2.5,
                linestyle="--",
                marker="s",
                markersize=4,
                label="100% CDI (mesmo valor no 1º dia)",
            )
            eixo.legend(loc="best", fontsize=11)
        eixo.set_title(titulo, fontsize=16, fontweight="bold")
        rotulo_eixo = "Preco de fechamento"
        if valores_cdi:
            rotulo_eixo = "Preco da acao e equivalente em 100% CDI"
        eixo.set_ylabel(rotulo_eixo, fontsize=12)
        eixo.set_xticks(indices)
        eixo.set_xticklabels(labels, rotation=25, ha="right", fontsize=9)
        eixo.grid(True, alpha=0.3, color=CORES["borda"])
        aplicar_tema_matplotlib(eixo, figura)
        figura.subplots_adjust(bottom=0.2, left=0.08, right=0.96, top=0.9)

        canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)
        configurar_tooltip_acao(canvas, eixo, linha, pontos_tooltip, simbolo, moeda)
        configurar_selecao_periodo(
            canvas,
            eixo,
            linha,
            pontos_tooltip,
            simbolo,
            moeda,
            self._atualizar_painel_pai,
            obter_quantidade_cotas=self._obter_quantidade_cotas,
        )
        self._publicar_resumo_periodo(canvas, pontos_tooltip, simbolo, moeda)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._figura = figura
        self._canvas = canvas

    def _publicar_resumo_periodo(
        self,
        canvas: FigureCanvasTkAgg,
        pontos: list[dict],
        simbolo: str,
        moeda: str,
    ) -> None:
        if len(pontos) < 2:
            return
        quantidade = self._obter_quantidade_cotas()
        payload = calcular_comparacao_acao_unica(
            pontos,
            simbolo,
            moeda,
            0,
            len(pontos) - 1,
            quantidade,
        )
        _publicar_payload_com_cdi(canvas, payload, self._atualizar_painel_pai)

    def _ajustar_grafico(self, tentativa: int = 0) -> None:
        if self._canvas is None or self._figura is None:
            if tentativa < 40:
                self.after(100, lambda: self._ajustar_grafico(tentativa + 1))
            return
        try:
            self._frame_grafico.update_idletasks()
            largura_px = max(600, self._frame_grafico.winfo_width() - 16)
            altura_px = max(450, self._frame_grafico.winfo_height() - 16)
            if largura_px < 500 and tentativa < 40:
                self.after(100, lambda: self._ajustar_grafico(tentativa + 1))
                return
            dpi = self._figura.get_dpi()
            self._figura.set_size_inches(largura_px / dpi, altura_px / dpi, forward=True)
            self._canvas.draw()
        except Exception:
            pass

    def _ao_fechar(self) -> None:
        if self._figura is not None:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
        self.destroy()


class JanelaGraficoAmpliadoComparacao(ctk.CTkToplevel):
    """Exibe o grafico de comparacao em tela maior."""

    def __init__(
        self,
        pai: ctk.CTk,
        titulo_janela: str,
        dados: dict,
        atualizar_painel_pai: Callable[[dict], None],
    ) -> None:
        super().__init__(pai)
        self._dados = dados
        self._atualizar_painel_pai = atualizar_painel_pai
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None

        self.title(titulo_janela)
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 620)

        self._montar_interface()
        configurar_janela_maximizada(self, ao_apos_layout=self._ajustar_grafico, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(120, self._ajustar_grafico)

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Comparacao de acoes — grafico ampliado",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Visualizacao ampliada do grafico comparativo. "
                "Clique em dois pontos para ver o resumo do intervalo na tela principal."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=960,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 10))

        self._frame_grafico = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._frame_grafico.pack(fill="both", expand=True, padx=16, pady=(8, 8))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=120,
        ).pack(side="right")

        self._desenhar_grafico()

    def _desenhar_grafico(self) -> None:
        for widget in self._frame_grafico.winfo_children():
            widget.destroy()

        if self._figura is not None:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
            self._canvas = None

        dados = self._dados
        simbolos = dados.get("simbolos") or []
        if not simbolos:
            return

        serie_referencia = dados["series"].get(simbolos[0]) or []
        if not serie_referencia:
            return

        self._frame_grafico.update_idletasks()
        largura_px = max(600, self._frame_grafico.winfo_width() - 16)
        altura_px = max(450, self._frame_grafico.winfo_height() - 16)
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
                color=_CORES_GRAFICO[i % len(_CORES_GRAFICO)],
                linewidth=2.5,
                marker="o",
                markersize=5,
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
                    markersize=5,
                )
        except Exception:
            pass

        eixo.set_xticks(indices)
        eixo.set_xticklabels(datas_grafico, rotation=30, ha="right", fontsize=10)
        eixo.set_title("Desempenho relativo no periodo", fontsize=16, fontweight="bold")
        eixo.set_ylabel("Indice relativo (base 100)", fontsize=12)
        eixo.legend(loc="best", fontsize=11)
        eixo.grid(True, alpha=0.3, color=CORES["borda"])
        aplicar_tema_matplotlib(eixo, figura)
        figura.subplots_adjust(bottom=0.2, left=0.08, right=0.96, top=0.92)

        canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)
        if linhas_plot:
            configurar_tooltip_comparacao(canvas, eixo, linhas_plot, dados["series"], simbolos)
            configurar_selecao_periodo_comparacao(
                canvas,
                eixo,
                linhas_plot,
                dados["series"],
                simbolos,
                self._atualizar_painel_pai,
            )
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._figura = figura
        self._canvas = canvas

    def _ajustar_grafico(self, tentativa: int = 0) -> None:
        if self._canvas is None or self._figura is None:
            if tentativa < 40:
                self.after(100, lambda: self._ajustar_grafico(tentativa + 1))
            return
        try:
            self._frame_grafico.update_idletasks()
            largura_px = max(600, self._frame_grafico.winfo_width() - 16)
            altura_px = max(450, self._frame_grafico.winfo_height() - 16)
            if largura_px < 500 and tentativa < 40:
                self.after(100, lambda: self._ajustar_grafico(tentativa + 1))
                return
            dpi = self._figura.get_dpi()
            self._figura.set_size_inches(largura_px / dpi, altura_px / dpi, forward=True)
            self._canvas.draw()
        except Exception:
            pass

    def _ao_fechar(self) -> None:
        if self._figura is not None:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
        self.destroy()


def atualizar_estado_botao_grafico_ampliado(botao: ctk.CTkButton, grafico_pronto: bool) -> None:
    """Habilita o botao quando o grafico ja foi carregado na tela principal."""
    botao.configure(state="normal" if grafico_pronto else "disabled")


def abrir_grafico_ampliado_acao(
    pai: ctk.CTk,
    titulo: str,
    dados_grafico: dict | None,
    obter_quantidade_cotas: Callable[[], int],
    atualizar_painel_pai: Callable[[dict], None],
) -> JanelaGraficoAmpliadoAcao | None:
    if not dados_grafico:
        return None
    return JanelaGraficoAmpliadoAcao(
        pai,
        titulo,
        dados_grafico,
        obter_quantidade_cotas,
        atualizar_painel_pai,
    )


def abrir_grafico_ampliado_comparacao(
    pai: ctk.CTk,
    titulo: str,
    dados: dict,
    atualizar_painel_pai: Callable[[dict], None],
) -> JanelaGraficoAmpliadoComparacao | None:
    simbolos = dados.get("simbolos") or []
    if not simbolos:
        return None
    return JanelaGraficoAmpliadoComparacao(pai, titulo, dados, atualizar_painel_pai)
