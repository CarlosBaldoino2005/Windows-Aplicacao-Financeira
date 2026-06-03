"""Janela dedicada para grafico de historico de uma acao."""
from __future__ import annotations

import threading

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Controller.controlador_mercado import ControladorMercado
from src.Tool.janela_helper import maximizar_janela
from src.Tool.validadores import validar_quantidade_cotas
from src.View.grafico_helper import configurar_selecao_periodo, configurar_tooltip_acao
from src.View.painel_comparacao_periodo import PainelComparacaoPeriodo, payload_instrucao
from src.View.tema import CORES

PERIODOS = [
    ("dia", "Dia"),
    ("semana", "Semana"),
    ("mes", "Mes"),
    ("trimestre", "Trimestre"),
    ("semestre", "Semestre"),
    ("ano", "Ano"),
    ("personalizado", "Personalizado"),
]

COR_GRAFICO = "#2563EB"


class JanelaGraficoAcao(ctk.CTkToplevel):
    """Tela ampla com periodo, grafico, tooltip e selecao de intervalo."""

    def __init__(self, pai: ctk.CTk, controlador: ControladorMercado, simbolo: str) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._simbolo = simbolo
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None

        codigo = simbolo.replace(".SA", "")
        self.title(f"Grafico da acao — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 600)

        self._montar_interface()
        self.after(0, lambda: maximizar_janela(self))
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(200, self._carregar_grafico)

    def _ao_fechar(self) -> None:
        if self._figura:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
        self.destroy()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        codigo = self._simbolo.replace(".SA", "")
        ctk.CTkLabel(
            cabecalho,
            text=f"Grafico — {codigo}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Passe o mouse para detalhes. Informe quantas acoes comprou e clique em 2 pontos "
                "no grafico para simular valor pago, valor final, lucro ou prejuizo."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(barra, text="Periodo").pack(side="left", padx=(0, 8))
        self._combo_periodo = ctk.CTkComboBox(
            barra,
            values=[p[1] for p in PERIODOS],
            width=140,
            command=self._alternar_datas,
        )
        self._combo_periodo.set("Mes")
        self._combo_periodo.pack(side="left", padx=(0, 16))

        ctk.CTkButton(
            barra,
            text="Atualizar grafico",
            command=self._carregar_grafico,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(barra, text="Qtd. de acoes").pack(side="left", padx=(0, 6))
        self._entrada_quantidade_cotas = ctk.CTkEntry(barra, width=90, justify="center")
        self._entrada_quantidade_cotas.insert(0, "100")
        self._entrada_quantidade_cotas.pack(side="left")

        self._frame_datas = ctk.CTkFrame(cabecalho, fg_color="transparent")
        ctk.CTkLabel(self._frame_datas, text="Inicio (dd/mm/aaaa)").pack(side="left", padx=16)
        self._entrada_inicio = ctk.CTkEntry(self._frame_datas, width=110)
        self._entrada_inicio.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(self._frame_datas, text="Fim (dd/mm/aaaa)").pack(side="left")
        self._entrada_fim = ctk.CTkEntry(self._frame_datas, width=110)
        self._entrada_fim.pack(side="left", padx=8)

        self._label_status = ctk.CTkLabel(
            cabecalho,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(anchor="w", padx=16, pady=(0, 4))

        self._frame_painel_periodo = ctk.CTkScrollableFrame(
            cabecalho,
            height=240,
            fg_color=CORES["fundo"],
            label_text="Resumo do periodo selecionado no grafico",
        )
        self._frame_painel_periodo.pack(fill="x", padx=16, pady=(0, 12))
        PainelComparacaoPeriodo.exibir(
            self._frame_painel_periodo,
            payload_instrucao(
                "Informe a quantidade de acoes. Clique no grafico: 1º ponto (inicio) "
                "e 2º ponto (fim) para ver valor pago, valor final, lucro ou prejuizo."
            ),
        )

        self._frame_grafico = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._frame_grafico.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["secundaria"],
            width=120,
        ).pack(side="right")

    def _periodo_chave(self) -> str:
        rotulo = self._combo_periodo.get()
        for chave, nome in PERIODOS:
            if nome == rotulo:
                return chave
        return "mes"

    def _ler_quantidade_cotas(self) -> int:
        quantidade, erro = validar_quantidade_cotas(self._entrada_quantidade_cotas.get())
        if erro:
            self._label_status.configure(text=erro, text_color=CORES["erro"])
            return 100
        return quantidade or 100

    def _alternar_datas(self, _valor=None) -> None:
        if self._periodo_chave() == "personalizado":
            self._frame_datas.pack(fill="x", pady=(0, 8))
        else:
            self._frame_datas.pack_forget()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        def trabalho():
            try:
                resultado = funcao()
                self.after(0, lambda: ao_concluir(resultado, None))
            except Exception as exc:
                self.after(0, lambda: ao_concluir(None, str(exc)))

        threading.Thread(target=trabalho, daemon=True).start()

    def _carregar_grafico(self) -> None:
        periodo = self._periodo_chave()
        self._label_status.configure(text="Gerando grafico...")

        def buscar():
            return self._controlador.obter_historico(
                self._simbolo,
                periodo,
                self._entrada_inicio.get(),
                self._entrada_fim.get(),
            )

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                return
            serie, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                return
            moeda = "BRL" if serie.simbolo.endswith(".SA") else "USD"
            pontos_tooltip = [
                {
                    "data": p.data_exibicao,
                    "fechamento": p.preco_fechamento,
                    "abertura": p.preco_abertura,
                    "volume": p.volume,
                }
                for p in serie.pontos
            ]
            self._desenhar_grafico(
                [p.data_exibicao for p in serie.pontos],
                [p.preco_fechamento for p in serie.pontos],
                f"{serie.simbolo.replace('.SA', '')} — {serie.periodo}",
                serie.simbolo,
                moeda,
                pontos_tooltip,
            )
            self._label_status.configure(text="Grafico atualizado.", text_color=CORES["sucesso"])

        self._executar_em_thread(buscar, ao_concluir)

    def _desenhar_grafico(
        self,
        labels: list,
        valores: list,
        titulo: str,
        simbolo: str,
        moeda: str,
        pontos_tooltip: list[dict],
    ) -> None:
        for widget in self._frame_grafico.winfo_children():
            widget.destroy()

        if self._figura:
            import matplotlib.pyplot as plt

            plt.close(self._figura)

        figura = Figure(figsize=(12, 7), dpi=100, facecolor=CORES["superficie"])
        eixo = figura.add_subplot(111)

        indices = np.arange(len(valores))
        linha, = eixo.plot(indices, valores, color=COR_GRAFICO, linewidth=2, marker="o", markersize=3)
        eixo.set_title(titulo, fontsize=14, fontweight="bold")
        eixo.set_ylabel("Preco de fechamento", fontsize=11)
        eixo.set_xticks(indices)
        eixo.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
        eixo.grid(True, alpha=0.3)
        figura.subplots_adjust(bottom=0.22, left=0.08, right=0.96, top=0.9)

        canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)

        def atualizar_painel(payload: dict) -> None:
            PainelComparacaoPeriodo.exibir(self._frame_painel_periodo, payload)

        configurar_tooltip_acao(canvas, eixo, linha, pontos_tooltip, simbolo, moeda)
        configurar_selecao_periodo(
            canvas,
            eixo,
            linha,
            pontos_tooltip,
            simbolo,
            moeda,
            atualizar_painel,
            obter_quantidade_cotas=self._ler_quantidade_cotas,
        )
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._figura = figura
        self._canvas = canvas
