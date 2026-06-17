"""Janela dedicada para visualizar o grafico de comparacao entre acoes."""
from __future__ import annotations

from typing import Any

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Service.cdi_servico import CdiServico
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.View.grafico_modelo_helper import (
    ModeloGrafico,
    desenhar_series_comparacao,
    montar_seletor_modelo_grafico,
    normalizar_modelo_grafico,
)
from src.View.grafico_helper import (
    COR_LINHA_CDI,
    TEXTO_INSTRUCAO_GRAFICO_COMPARACAO,
    aplicar_tema_matplotlib,
    configurar_selecao_periodo_comparacao,
    configurar_tooltip_comparacao,
)
from src.View.destaque_cotacao_helper import (
    PainelDestaqueCotacao,
    iniciar_atualizacao_destaque_multiplo,
)
from src.View.grafico_zoom_helper import criar_controle_zoom, montar_botoes_zoom_grafico
from src.View.janela_grafico_ampliado import (
    abrir_grafico_ampliado_comparacao,
    atualizar_estado_botao_grafico_ampliado,
)
from src.View.janela_resumo_periodo import (
    abrir_janela_resumo_periodo,
    atualizar_estado_botao_resumo_ampliado,
)
from src.View.painel_comparacao_periodo import PainelComparacaoPeriodo, payload_instrucao
from src.View.tema import CORES

CORES_GRAFICO = ["#2563EB", "#16A34A", "#D97706", "#DC2626", "#7C3AED", "#0891B2"]


class JanelaGraficoComparacao(ctk.CTkToplevel):
    """Tela ampla com grafico, tooltip e selecao vermelha por periodo."""

    def __init__(
        self,
        pai: ctk.CTk,
        dados: dict,
        rotulo_periodo: str,
        controlador: Any | None = None,
    ) -> None:
        super().__init__(pai)
        self._dados = dados
        self._controlador = controlador
        self._rotulo_periodo = rotulo_periodo
        self._janela_resumo_periodo: ctk.CTkToplevel | None = None
        self._janela_grafico_ampliado: ctk.CTkToplevel | None = None
        self._controle_zoom = None
        simbolos_txt = ", ".join(s.replace(".SA", "") for s in dados["simbolos"])
        self.title(f"Comparacao de acoes — {rotulo_periodo} — {simbolos_txt}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 600)

        self._figura = None
        self._canvas = None
        self._desenhando_grafico = False
        self._modelo_grafico: ModeloGrafico = normalizar_modelo_grafico(
            dados.get("modelo_grafico")
        )
        self._dados["modelo_grafico"] = self._modelo_grafico

        self._montar_interface()
        configurar_janela_maximizada(self, ao_apos_layout=self._desenhar_grafico)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        if self._controlador is not None:
            self._atualizar_destaque_cotacao()

    def _montar_interface(self) -> None:
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
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
                "Use Zoom -/+ ou a roda do mouse. Apos ampliar, arraste o grafico para mover. "
                "Passe o mouse para detalhes. "
                "Linha laranja tracejada: 100% CDI (indice base 100). "
                "Clique em 2 pontos para comparar o intervalo (marcadores vermelhos)."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self._painel_destaque_cotacao = PainelDestaqueCotacao(cabecalho, modo_multiplo=True)
        self._painel_destaque_cotacao.pack(fill="x", padx=16, pady=(0, 10))

        barra_resumo = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_resumo.pack(fill="x", padx=16, pady=(0, 4))
        self._btn_resumo_ampliado = ctk.CTkButton(
            barra_resumo,
            text="Ver resumo ampliado",
            width=170,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            command=self._abrir_resumo_periodo_ampliado,
            state="disabled",
        )
        self._btn_resumo_ampliado.pack(side="right")

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
        self._payload_resumo_periodo = payload_instrucao(texto_painel)
        self._exibir_resumo_comparacao(self._payload_resumo_periodo)

        barra_grafico = ctk.CTkFrame(self, fg_color="transparent")
        barra_grafico.pack(fill="x", padx=16, pady=(4, 0))
        montar_seletor_modelo_grafico(
            barra_grafico,
            modelo_inicial=self._modelo_grafico,
            ao_mudar=self._alternar_modelo_grafico,
        )
        montar_botoes_zoom_grafico(barra_grafico, lambda: self._controle_zoom)
        self._btn_grafico_ampliado = ctk.CTkButton(
            barra_grafico,
            text="Ver grafico ampliado",
            width=170,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            command=self._abrir_grafico_ampliado,
            state="disabled",
        )
        self._btn_grafico_ampliado.pack(side="right")

        self._frame_grafico = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._frame_grafico.pack(side="top", fill="both", expand=True, padx=16, pady=(8, 8))

    def _alternar_modelo_grafico(self, modelo: ModeloGrafico) -> None:
        self._modelo_grafico = modelo
        self._dados["modelo_grafico"] = modelo
        self._desenhar_grafico()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _atualizar_destaque_cotacao(self) -> None:
        simbolos = self._dados.get("simbolos") or []
        if not simbolos or self._controlador is None:
            return
        iniciar_atualizacao_destaque_multiplo(
            self._painel_destaque_cotacao,
            self._controlador,
            simbolos,
            self._executar_em_thread,
        )

    def _exibir_resumo_comparacao(self, payload: dict) -> None:
        self._payload_resumo_periodo = payload
        PainelComparacaoPeriodo.exibir(self._frame_painel_resultado, payload)
        atualizar_estado_botao_resumo_ampliado(self._btn_resumo_ampliado, payload)

    def _atualizar_painel_comparacao(self, payload: dict) -> None:
        self._exibir_resumo_comparacao(payload)

    def _abrir_grafico_ampliado(self) -> None:
        if self._janela_grafico_ampliado is not None:
            try:
                if self._janela_grafico_ampliado.winfo_exists():
                    self._janela_grafico_ampliado.focus_force()
                    return
            except Exception:
                pass
        simbolos_txt = ", ".join(s.replace(".SA", "") for s in self._dados["simbolos"])
        titulo = f"Grafico ampliado — {self._rotulo_periodo} — {simbolos_txt}"
        self._janela_grafico_ampliado = abrir_grafico_ampliado_comparacao(
            self,
            titulo,
            self._dados,
            self._exibir_resumo_comparacao,
        )

    def _abrir_resumo_periodo_ampliado(self) -> None:
        if self._janela_resumo_periodo is not None:
            try:
                if self._janela_resumo_periodo.winfo_exists():
                    self._janela_resumo_periodo.focus_force()
                    return
            except Exception:
                pass
        simbolos_txt = ", ".join(s.replace(".SA", "") for s in self._dados["simbolos"])
        titulo = f"Resumo da comparacao — {self._rotulo_periodo} — {simbolos_txt}"
        self._janela_resumo_periodo = abrir_janela_resumo_periodo(
            self, self._payload_resumo_periodo, titulo
        )

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
            self._controle_zoom = None

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

        indices = np.arange(len(serie_referencia))
        datas_grafico = [p["data"] for p in serie_referencia]

        linhas_plot = desenhar_series_comparacao(
            eixo,
            indices,
            simbolos,
            dados["series"],
            CORES_GRAFICO,
            modelo=self._modelo_grafico,
        )

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
        eixo.grid(True, alpha=0.3, color=CORES["borda"])
        aplicar_tema_matplotlib(eixo, figura)
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
        self._controle_zoom = criar_controle_zoom(self._canvas, eixo)
        atualizar_estado_botao_grafico_ampliado(self._btn_grafico_ampliado, True)

    def _ao_fechar(self) -> None:
        if self._janela_grafico_ampliado is not None:
            try:
                if self._janela_grafico_ampliado.winfo_exists():
                    self._janela_grafico_ampliado.destroy()
            except Exception:
                pass
        if self._janela_resumo_periodo is not None:
            try:
                if self._janela_resumo_periodo.winfo_exists():
                    self._janela_resumo_periodo.destroy()
            except Exception:
                pass
        if self._figura:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
        self.destroy()
