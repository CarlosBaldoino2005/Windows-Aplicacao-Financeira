"""Janela dedicada para grafico de historico de uma acao."""
from __future__ import annotations

import threading

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Controller.controlador_mercado import ControladorMercado
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import configurar_janela_maximizada
from src.Tool.validadores import validar_quantidade_cotas
from src.Service.cdi_servico import CdiServico
from src.View.grafico_helper import (
    COR_LINHA_CDI,
    TEXTO_INSTRUCAO_GRAFICO_ACAO,
    configurar_selecao_periodo,
    configurar_tooltip_acao,
)
from src.View.janela_detalhes_acao import JanelaDetalhesAcao
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

class JanelaGraficoAcao(ctk.CTkToplevel):
    """Tela ampla com periodo, grafico, tooltip e selecao de intervalo."""

    def __init__(self, pai: ctk.CTk, controlador: ControladorMercado, simbolo: str) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._simbolo = simbolo
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._janela_detalhes: JanelaDetalhesAcao | None = None
        self._config_ini = ConfigPainelIni()

        codigo = simbolo.replace(".SA", "")
        self.title(f"Grafico da acao — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 600)

        self._montar_interface()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(200, self._carregar_grafico)

    def _ao_fechar(self) -> None:
        self._persistir_quantidade_cotas_ini()
        if self._janela_detalhes is not None:
            try:
                if self._janela_detalhes.winfo_exists():
                    self._janela_detalhes.destroy()
            except Exception:
                pass
        if self._figura:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
        self.destroy()

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
                "Passe o mouse para detalhes. Linha laranja tracejada: rendimento em 100% CDI "
                "(mesmo valor do 1º dia). Informe quantas acoes e clique em 2 pontos para simular "
                "valor pago, valor final, lucro ou prejuizo."
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
        qtd_ini = self._config_ini.carregar_quantidade_cotas_grafico()
        self._entrada_quantidade_cotas.insert(0, str(qtd_ini))
        self._entrada_quantidade_cotas.pack(side="left", padx=(0, 16))

        ctk.CTkButton(
            barra,
            text="Mais detalhes",
            command=self._abrir_mais_detalhes,
            fg_color=CORES["secundaria"],
            hover_color=CORES["primariaHover"],
            width=130,
        ).pack(side="left")

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
            payload_instrucao(TEXTO_INSTRUCAO_GRAFICO_ACAO),
        )

        self._frame_grafico = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._frame_grafico.pack(side="top", fill="both", expand=True, padx=16, pady=(8, 8))

    def _periodo_chave(self) -> str:
        rotulo = self._combo_periodo.get()
        for chave, nome in PERIODOS:
            if nome == rotulo:
                return chave
        return "mes"

    def _abrir_mais_detalhes(self) -> None:
        if self._janela_detalhes is not None:
            try:
                if self._janela_detalhes.winfo_exists():
                    self._janela_detalhes.focus_force()
                    return
            except Exception:
                pass
        self._janela_detalhes = JanelaDetalhesAcao(self, self._controlador, self._simbolo)

    def _ler_quantidade_cotas(self) -> tuple[int | None, str | None]:
        padrao = self._config_ini.padrao_cotas_grafico()
        return validar_quantidade_cotas(
            self._entrada_quantidade_cotas.get(),
            padrao=padrao,
        )

    def _persistir_quantidade_cotas_ini(self) -> None:
        quantidade, erro = self._ler_quantidade_cotas()
        if erro or quantidade is None:
            return
        try:
            self._config_ini.salvar_quantidade_cotas_grafico(quantidade)
        except OSError:
            pass

    def _obter_quantidade_cotas_para_grafico(self) -> int:
        quantidade, erro = self._ler_quantidade_cotas()
        if erro:
            self._label_status.configure(text=erro, text_color=CORES["erro"])
            return self._config_ini.padrao_cotas_grafico()
        return quantidade or self._config_ini.padrao_cotas_grafico()

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
        quantidade, erro_qtd = self._ler_quantidade_cotas()
        if erro_qtd:
            self._label_status.configure(text=erro_qtd, text_color=CORES["erro"])
            return
        if quantidade is not None:
            try:
                self._config_ini.salvar_quantidade_cotas_grafico(quantidade)
            except OSError:
                self._label_status.configure(
                    text="Nao foi possivel salvar a quantidade no painel.ini.",
                    text_color=CORES["erro"],
                )
                return

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
            valores_cdi = None
            if moeda == "BRL":
                valores_cdi = CdiServico().montar_linha_preco_equivalente_cdi(pontos_tooltip)
            codigo_grafico = serie.simbolo.replace(".SA", "").replace("-USD", "")
            self._desenhar_grafico(
                [p.data_exibicao for p in serie.pontos],
                [p.preco_fechamento for p in serie.pontos],
                f"{codigo_grafico} — {serie.periodo}",
                serie.simbolo,
                moeda,
                pontos_tooltip,
                valores_cdi=valores_cdi,
            )
            if getattr(serie, "aviso", ""):
                self._label_status.configure(
                    text=serie.aviso,
                    text_color=CORES["aviso"],
                )
            else:
                self._label_status.configure(
                    text="Grafico atualizado.",
                    text_color=CORES["sucesso"],
                )

        self._executar_em_thread(buscar, ao_concluir)

    def _desenhar_grafico(
        self,
        labels: list,
        valores: list,
        titulo: str,
        simbolo: str,
        moeda: str,
        pontos_tooltip: list[dict],
        valores_cdi: list[float] | None = None,
    ) -> None:
        for widget in self._frame_grafico.winfo_children():
            widget.destroy()

        if self._figura:
            import matplotlib.pyplot as plt

            plt.close(self._figura)

        largura_px = max(400, self._frame_grafico.winfo_width() - 16)
        altura_px = max(300, self._frame_grafico.winfo_height() - 16)
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
            linewidth=2,
            marker="o",
            markersize=3,
            label="Acao (fechamento)",
        )
        if valores_cdi and len(valores_cdi) == len(valores):
            eixo.plot(
                indices,
                valores_cdi,
                color=COR_LINHA_CDI,
                linewidth=2,
                linestyle="--",
                marker="s",
                markersize=3,
                label="100% CDI (mesmo valor no 1º dia)",
            )
            eixo.legend(loc="best", fontsize=9)
        eixo.set_title(titulo, fontsize=14, fontweight="bold")
        rotulo_eixo = "Preco de fechamento"
        if valores_cdi:
            rotulo_eixo = "Preco da acao e equivalente em 100% CDI"
        eixo.set_ylabel(rotulo_eixo, fontsize=11)
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
            obter_quantidade_cotas=self._obter_quantidade_cotas_para_grafico,
        )
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._figura = figura
        self._canvas = canvas
