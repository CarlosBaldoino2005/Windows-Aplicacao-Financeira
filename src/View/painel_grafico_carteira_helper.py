"""Painel de grafico comparativo dos ativos da carteira (padrao das telas de mercado)."""
from __future__ import annotations

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import LinhaCarteira
from src.Model.periodos_mercado import PERIODOS_MERCADO, periodo_chave_por_rotulo
from src.Service.cdi_servico import CdiServico
from src.Tool.janela_helper import executar_em_thread, janela_ui_ainda_ativa
from src.View.grafico_modelo_helper import (
    ModeloGrafico,
    desenhar_series_comparacao,
    montar_seletor_modelo_grafico,
)
from src.View.grafico_helper import (
    COR_LINHA_CDI,
    MARGEM_GRAFICO_BOTTOM_ROTULOS,
    configurar_selecao_periodo_comparacao,
    configurar_tooltip_comparacao,
    finalizar_figura_grafico,
)
from src.View.grafico_zoom_helper import criar_controle_zoom, montar_botoes_zoom_grafico
from src.View.janela_grafico_comparacao import CORES_GRAFICO, JanelaGraficoComparacao
from src.View.tema import CORES

ALTURA_GRAFICO_PX = 360


class PainelGraficoCarteira:
    """Grafico comparativo (indice base 100) dos ativos cadastrados na carteira."""

    def __init__(
        self,
        janela_pai: ctk.CTkToplevel,
        controlador: ControladorCarteira,
        *,
        modo_janela: bool = False,
    ) -> None:
        self._janela = janela_pai
        self._controlador = controlador
        self._modo_janela = modo_janela
        self._raiz: ctk.CTkFrame | None = None
        self._frame_grafico: ctk.CTkFrame | None = None
        self._label_status: ctk.CTkLabel | None = None
        self._combo_periodo: ctk.CTkComboBox | None = None
        self._entrada_inicio: ctk.CTkEntry | None = None
        self._entrada_fim: ctk.CTkEntry | None = None
        self._frame_datas: ctk.CTkFrame | None = None
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._controle_zoom = None
        self._dados_grafico: dict | None = None
        self._carregando = False
        self._desenhando = False
        self._tem_posicoes = False
        self._janela_grafico_ampliado: JanelaGraficoComparacao | None = None
        self._modelo_grafico: ModeloGrafico = "area"

    def montar(self, pai: ctk.CTkFrame) -> ctk.CTkFrame:
        """Monta o painel; o chamador posiciona o card retornado (ex.: grid row=1)."""
        card = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=12)
        self._raiz = card

        ctk.CTkLabel(
            card,
            text="Grafico da carteira (indice base 100 no 1º dia)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            card,
            text=(
                "Compara o desempenho dos ativos da carteira no periodo. "
                "Use Zoom -/+ ou a roda do mouse. Passe o mouse para detalhes. "
                "Linha laranja tracejada: 100% CDI."
            ),
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 8))

        barra = ctk.CTkFrame(card, fg_color="transparent")
        barra.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(barra, text="Periodo").pack(side="left", padx=(0, 8))
        self._combo_periodo = ctk.CTkComboBox(
            barra,
            values=[p[1] for p in PERIODOS_MERCADO],
            width=130,
            command=self._alternar_datas,
        )
        self._combo_periodo.set("Mes")
        self._combo_periodo.pack(side="left", padx=(0, 10))

        montar_seletor_modelo_grafico(
            barra,
            modelo_inicial=self._modelo_grafico,
            ao_mudar=self._alternar_modelo_grafico,
            largura_combo=110,
        )

        ctk.CTkButton(
            barra,
            text="Atualizar grafico",
            command=self._carregar_grafico,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=140,
            height=32,
        ).pack(side="left", padx=(0, 10))

        if not self._modo_janela:
            ctk.CTkButton(
                barra,
                text="Abrir em tela cheia",
                command=self._abrir_tela_cheia,
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=150,
                height=32,
            ).pack(side="left")

        self._frame_datas = ctk.CTkFrame(card, fg_color="transparent")
        ctk.CTkLabel(self._frame_datas, text="Inicio (dd/mm/aaaa)").pack(side="left", padx=(12, 4))
        self._entrada_inicio = ctk.CTkEntry(self._frame_datas, width=110)
        self._entrada_inicio.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(self._frame_datas, text="Fim (dd/mm/aaaa)").pack(side="left", padx=(0, 4))
        self._entrada_fim = ctk.CTkEntry(self._frame_datas, width=110)
        self._entrada_fim.pack(side="left", padx=(0, 12))

        self._label_status = ctk.CTkLabel(
            card,
            text="Cadastre posicoes na carteira para ver o grafico.",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(anchor="w", padx=12, pady=(0, 4))

        barra_zoom = ctk.CTkFrame(card, fg_color="transparent")
        barra_zoom.pack(fill="x", padx=12, pady=(0, 4))
        montar_botoes_zoom_grafico(barra_zoom, lambda: self._controle_zoom)

        self._frame_grafico = ctk.CTkFrame(
            card,
            fg_color=CORES["fundo"],
            corner_radius=8,
            **({} if self._modo_janela else {"height": ALTURA_GRAFICO_PX}),
        )
        if self._modo_janela:
            self._frame_grafico.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        else:
            self._frame_grafico.pack(fill="x", padx=12, pady=(0, 12))
            self._frame_grafico.pack_propagate(False)

        return card

    def reaplicar_layout(self) -> None:
        """Redesenha o grafico apos o layout da janela estabilizar."""
        if self._dados_grafico and self._tem_posicoes:
            self._desenhar_grafico()

    def liberar(self) -> None:
        """Fecha recursos Matplotlib ao fechar a janela da carteira."""
        if self._janela_grafico_ampliado is not None:
            try:
                if self._janela_grafico_ampliado.winfo_exists():
                    self._janela_grafico_ampliado._ao_fechar()
            except Exception:
                pass
        self._limpar_figura()

    def atualizar_linhas(self, linhas: list[LinhaCarteira]) -> None:
        """Recarrega o grafico quando a lista da carteira muda."""
        self._tem_posicoes = bool(linhas)
        if not linhas:
            self._dados_grafico = None
            self._limpar_figura()
            if self._label_status is not None:
                self._label_status.configure(
                    text="Cadastre posicoes na carteira para ver o grafico.",
                    text_color=CORES["textoSecundario"],
                )
            return
        self._carregar_grafico()

    def _alternar_modelo_grafico(self, modelo: ModeloGrafico) -> None:
        self._modelo_grafico = modelo
        if self._dados_grafico:
            self._dados_grafico["modelo_grafico"] = modelo
            self._desenhar_grafico()

    def _alternar_datas(self, _valor: str | None = None) -> None:
        if self._frame_datas is None or self._combo_periodo is None:
            return
        if self._combo_periodo.get() == "Personalizado":
            self._frame_datas.pack(fill="x", pady=(0, 4))
        else:
            self._frame_datas.pack_forget()

    def _periodo_chave(self) -> str:
        if self._combo_periodo is None:
            return "mes"
        return periodo_chave_por_rotulo(self._combo_periodo.get())

    def _carregar_grafico(self) -> None:
        if not self._tem_posicoes or self._carregando:
            return
        if not janela_ui_ainda_ativa(self._janela):
            return

        periodo = self._periodo_chave()
        data_ini = self._entrada_inicio.get().strip() if self._entrada_inicio else ""
        data_fim = self._entrada_fim.get().strip() if self._entrada_fim else ""

        self._carregando = True
        if self._label_status is not None:
            self._label_status.configure(
                text="Carregando historico dos ativos...",
                text_color=CORES["textoSecundario"],
            )

        def buscar():
            return self._controlador.comparar_ativos_carteira(periodo, data_ini, data_fim)

        def ao_concluir(resultado, erro_thread):
            self._carregando = False
            if not janela_ui_ainda_ativa(self._janela):
                return
            if erro_thread:
                self._limpar_figura()
                if self._label_status is not None:
                    self._label_status.configure(text=erro_thread, text_color=CORES["erro"])
                return

            dados, msg_erro = resultado if resultado is not None else (None, "Erro ao carregar grafico.")
            if msg_erro or dados is None:
                self._limpar_figura()
                if self._label_status is not None:
                    self._label_status.configure(
                        text=msg_erro or "Nao foi possivel montar o grafico.",
                        text_color=CORES["erro"],
                    )
                return

            self._dados_grafico = dados
            self._dados_grafico["modelo_grafico"] = self._modelo_grafico
            avisos = dados.get("avisos") or []
            qtd = len(dados.get("simbolos") or [])
            status = f"{qtd} ativo(s) no grafico — periodo: {self._combo_periodo.get() if self._combo_periodo else 'Mes'}."
            if avisos:
                status += " Avisos: " + " | ".join(avisos)
            if self._label_status is not None:
                self._label_status.configure(text=status, text_color=CORES["sucesso"])
            self._janela.after(50, self._desenhar_grafico)

        executar_em_thread(self._janela, buscar, ao_concluir)

    def _abrir_tela_cheia(self) -> None:
        if not self._dados_grafico or not self._dados_grafico.get("simbolos"):
            if self._label_status is not None:
                self._label_status.configure(
                    text="Atualize o grafico antes de abrir em tela cheia.",
                    text_color=CORES["aviso"],
                )
            return

        if self._janela_grafico_ampliado is not None:
            try:
                if self._janela_grafico_ampliado.winfo_exists():
                    self._janela_grafico_ampliado._ao_fechar()
            except Exception:
                pass

        rotulo = self._combo_periodo.get() if self._combo_periodo else "Mes"
        self._janela_grafico_ampliado = JanelaGraficoComparacao(
            self._janela,
            self._dados_grafico,
            rotulo,
            controlador=None,
        )
        self._janela_grafico_ampliado.title(f"Carteira — comparacao — {rotulo}")

    def _limpar_figura(self) -> None:
        if self._canvas is not None:
            try:
                self._canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self._canvas = None
        if self._frame_grafico is not None:
            for widget in self._frame_grafico.winfo_children():
                widget.destroy()
        if self._figura is not None:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
            self._controle_zoom = None

    def _area_grafico_valida(self) -> bool:
        if self._frame_grafico is None:
            return False
        try:
            return self._frame_grafico.winfo_width() > 80 and self._frame_grafico.winfo_height() > 80
        except Exception:
            return False

    def _desenhar_grafico(self, tentativa: int = 0) -> None:
        if self._desenhando and tentativa == 0:
            self._janela.after(100, lambda: self._desenhar_grafico(0))
            return
        if not self._area_grafico_valida():
            if tentativa < 30:
                self._janela.after(80, lambda: self._desenhar_grafico(tentativa + 1))
            return
        self._desenhando = True
        try:
            self._montar_figura()
        finally:
            self._desenhando = False

    def _montar_figura(self) -> None:
        if self._frame_grafico is None or not self._dados_grafico:
            return

        self._limpar_figura()
        dados = self._dados_grafico
        simbolos = dados.get("simbolos") or []
        if not simbolos:
            return

        serie_referencia = dados["series"].get(simbolos[0]) or []
        if not serie_referencia:
            return

        largura_px = max(400, self._frame_grafico.winfo_width() - 16)
        altura_px = max(260, self._frame_grafico.winfo_height() - 16)
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
                    linewidth=2.2,
                    linestyle="--",
                    marker="s",
                    markersize=3,
                )
        except Exception:
            pass

        eixo.set_xticks(indices)
        eixo.set_xticklabels(datas_grafico, rotation=30, ha="right", fontsize=8)
        eixo.set_ylabel("Indice relativo (base 100)", fontsize=10)
        eixo.legend(loc="best", fontsize=9)
        finalizar_figura_grafico(
            eixo,
            figura,
            "Desempenho relativo dos ativos da carteira",
            bottom=MARGEM_GRAFICO_BOTTOM_ROTULOS,
        )

        self._figura = figura
        self._canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

        if linhas_plot:
            configurar_tooltip_comparacao(
                self._canvas, eixo, linhas_plot, dados["series"], simbolos
            )

            def _atualizar_painel(_payload: dict) -> None:
                pass

            configurar_selecao_periodo_comparacao(
                self._canvas,
                eixo,
                linhas_plot,
                dados["series"],
                simbolos,
                _atualizar_painel,
            )

        self._canvas.draw()
        self._controle_zoom = criar_controle_zoom(self._canvas, eixo)
