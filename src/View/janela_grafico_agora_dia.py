"""Janela Agora para um dia historico (intraday e variacao do pregão)."""
from __future__ import annotations

from datetime import date

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Model.agora_dia_historico import ResumoDiaAgora
from src.Service.agora_historico_dia_servico import AgoraHistoricoDiaServico
from src.Tool.cotacao_dual_helper import codigo_exibicao, rotulo_tipo_ativo
from src.Tool.dia_util_helper import formatar_data_ptbr
from src.Tool.janela_helper import (
    configurar_janela_maximizada,
    executar_em_thread,
    janela_ui_ainda_ativa,
)
from src.View.agora_painel_metricas_dia_helper import PainelMetricasDiaAgora
from src.View.formatadores import formatar_moeda, formatar_variacao_com_rotulo
from src.View.grafico_agora_helper import (
    calcular_limites_eixo_agora,
    configurar_eixo_intraday_agora,
    desenhar_linha_fechamento_anterior,
    desenhar_serie_agora,
    obter_cor_tendencia_agora,
)
from src.View.grafico_helper import (
    configurar_tooltip_acao,
    extrair_minutos_dia_de_ponto,
    finalizar_figura_grafico,
)
from src.View.grafico_modelo_helper import ModeloGrafico, montar_seletor_modelo_grafico
from src.View.grafico_zoom_helper import criar_controle_zoom, montar_botoes_zoom_grafico
from src.View.tema import CORES

ALTURA_GRAFICO_MINIMA_PX = 280


class JanelaGraficoAgoraDia(ctk.CTkToplevel):
    """Exibe intraday e variacao de um dia passado, no estilo da tela Agora."""

    def __init__(
        self,
        pai: ctk.CTk,
        simbolo: str,
        data_ref: date,
    ) -> None:
        super().__init__(pai)
        self._simbolo = simbolo
        self._data_ref = data_ref
        self._servico = AgoraHistoricoDiaServico()
        self._resumo_dia: ResumoDiaAgora | None = None
        self._pontos_intraday = None
        self._modelo_grafico: ModeloGrafico = "area"
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._eixo = None
        self._controle_zoom = None
        self._carregando = False
        self._painel_metricas: PainelMetricasDiaAgora | None = None

        codigo = codigo_exibicao(simbolo)
        self.title(f"Agora — {codigo} — {formatar_data_ptbr(data_ref)}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 650)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.after(200, self._carregar_dados)

    def _ao_fechar(self) -> None:
        if self._figura is not None:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
        self.destroy()

    def _montar_interface(self) -> None:
        self.grid_rowconfigure(1, weight=1, minsize=ALTURA_GRAFICO_MINIMA_PX)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.grid(row=0, column=0, sticky="ew")

        barra_topo = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_topo.pack(fill="x", padx=16, pady=(12, 4))

        codigo = codigo_exibicao(self._simbolo)
        tipo = rotulo_tipo_ativo(self._simbolo)
        ctk.CTkLabel(
            barra_topo,
            text=f"{codigo}  ·  {tipo}  ·  {formatar_data_ptbr(self._data_ref)}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")

        ctk.CTkLabel(
            barra_topo,
            text="DIA HISTORICO",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            fg_color=CORES["primaria"],
            corner_radius=6,
            width=120,
            height=26,
        ).pack(side="left", padx=(12, 0))

        barra_modelo = ctk.CTkFrame(barra_topo, fg_color="transparent")
        barra_modelo.pack(side="right")
        montar_seletor_modelo_grafico(
            barra_modelo,
            modelo_inicial=self._modelo_grafico,
            ao_mudar=self._alternar_modelo_grafico,
            largura_combo=110,
        )

        painel_preco = ctk.CTkFrame(
            cabecalho,
            fg_color=CORES.get("infoFundo", CORES["fundo"]),
            corner_radius=10,
            border_width=2,
            border_color=CORES["primaria"],
        )
        painel_preco.pack(fill="x", padx=16, pady=(4, 8))

        linha_preco = ctk.CTkFrame(painel_preco, fg_color="transparent")
        linha_preco.pack(fill="x", padx=16, pady=(10, 4))

        self._label_preco = ctk.CTkLabel(
            linha_preco,
            text="—",
            font=ctk.CTkFont(size=40, weight="bold"),
            text_color=CORES["texto"],
        )
        self._label_preco.pack(side="left", anchor="s", pady=(0, 2))

        self._frame_indicadores = ctk.CTkFrame(linha_preco, fg_color="transparent")
        self._frame_indicadores.pack(side="left", anchor="s", padx=(20, 0), pady=(0, 4))

        self._label_variacao_dia = ctk.CTkLabel(
            self._frame_indicadores,
            text="Carregando...",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=CORES["textoSecundario"],
            anchor="w",
        )
        self._label_variacao_dia.pack(anchor="w")

        self._painel_metricas = PainelMetricasDiaAgora(painel_preco)
        self._painel_metricas.montar().pack(fill="x", padx=16, pady=(0, 10))

        self._container_grafico = ctk.CTkFrame(self, fg_color="transparent")
        self._container_grafico.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        self._container_grafico.grid_rowconfigure(2, weight=1)
        self._container_grafico.grid_columnconfigure(0, weight=1)

        self._label_status = ctk.CTkLabel(
            self._container_grafico,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            anchor="w",
        )
        self._label_status.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        self._barra_zoom = ctk.CTkFrame(self._container_grafico, fg_color="transparent")
        self._barra_zoom.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        self._controle_zoom = None

        self._frame_grafico = ctk.CTkFrame(
            self._container_grafico,
            fg_color=CORES["superficie"],
            corner_radius=8,
        )
        self._frame_grafico.grid(row=2, column=0, sticky="nsew")
        self._frame_grafico.grid_rowconfigure(0, weight=1)
        self._frame_grafico.grid_columnconfigure(0, weight=1)

    def _carregar_dados(self) -> None:
        if self._carregando or not janela_ui_ainda_ativa(self):
            return
        self._carregando = True
        self._label_status.configure(text="Carregando dados do dia...")

        def buscar():
            serie, erro = self._servico.buscar_serie_dia(self._simbolo, self._data_ref)
            if erro or serie is None:
                raise RuntimeError(erro or "Sem dados para o dia.")
            resumo = self._servico.montar_resumo_dia(self._simbolo, self._data_ref, serie.pontos)
            if resumo is None:
                raise RuntimeError("Nao foi possivel calcular o resumo do dia.")
            return serie, resumo

        def ao_concluir(resultado, erro_thread):
            self._carregando = False
            if not janela_ui_ainda_ativa(self):
                return
            if erro_thread:
                self._label_status.configure(text=f"Erro: {erro_thread}", text_color=CORES["erro"])
                return
            if resultado is None:
                self._label_status.configure(text="Dados indisponiveis.", text_color=CORES["erro"])
                return
            try:
                serie, resumo = resultado
            except (TypeError, ValueError) as exc:
                self._label_status.configure(
                    text=f"Erro ao processar dados: {exc}",
                    text_color=CORES["erro"],
                )
                return
            self._resumo_dia = resumo
            self._pontos_intraday = serie.pontos
            self._atualizar_painel_preco(resumo)
            self._desenhar_grafico(serie.pontos, resumo)
            self._label_status.configure(
                text=f"Dia {formatar_data_ptbr(self._data_ref)} · {len(serie.pontos)} pontos intraday",
                text_color=CORES["textoSecundario"],
            )

        executar_em_thread(self, buscar, ao_concluir)

    def _atualizar_painel_preco(self, resumo: ResumoDiaAgora) -> None:
        moeda = resumo.moeda
        self._label_preco.configure(text=formatar_moeda(resumo.fechamento, moeda))
        cor = CORES["sucesso"] if resumo.variacao_valor >= 0 else CORES["erro"]
        self._label_variacao_dia.configure(
            text=formatar_variacao_com_rotulo(
                resumo.variacao_valor,
                resumo.variacao_pct,
                "Variacao do dia",
                moeda,
            ),
            text_color=cor,
        )

        if self._painel_metricas is not None:
            self._painel_metricas.atualizar(resumo)

    def _alternar_modelo_grafico(self, modelo: ModeloGrafico) -> None:
        self._modelo_grafico = modelo
        if self._resumo_dia is not None and self._pontos_intraday:
            self._desenhar_grafico(self._pontos_intraday, self._resumo_dia)

    def _montar_serie_intraday(self, pontos) -> tuple[list[float], list[float], list[dict]]:
        posicoes_x: list[float] = []
        valores: list[float] = []
        pontos_tooltip: list[dict] = []

        for ponto in pontos:
            minutos = extrair_minutos_dia_de_ponto(ponto.data_exibicao, data_iso=ponto.data_iso)
            if minutos is None:
                continue
            posicoes_x.append(minutos)
            valores.append(ponto.preco_fechamento)
            pontos_tooltip.append(
                {
                    "data": ponto.data_exibicao,
                    "data_iso": ponto.data_iso,
                    "fechamento": ponto.preco_fechamento,
                    "abertura": ponto.preco_abertura,
                    "maxima": ponto.preco_maxima,
                    "minima": ponto.preco_minima,
                    "volume": ponto.volume,
                    "minutos_dia": minutos,
                }
            )
        return posicoes_x, valores, pontos_tooltip

    def _desenhar_grafico(self, pontos, resumo: ResumoDiaAgora) -> None:
        posicoes_x, valores, pontos_tooltip = self._montar_serie_intraday(pontos)
        if not valores:
            self._label_status.configure(
                text="Grafico indisponivel (horarios invalidos).",
                text_color=CORES["erro"],
            )
            return

        if self._canvas is not None:
            try:
                self._canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self._canvas = None
        for widget in self._frame_grafico.winfo_children():
            widget.destroy()
        if self._figura is not None:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
        self._controle_zoom = None

        largura_px = max(400, self._frame_grafico.winfo_width() - 16)
        altura_px = max(200, self._frame_grafico.winfo_height() - 16)
        dpi = 100
        figura = Figure(
            figsize=(largura_px / dpi, altura_px / dpi),
            dpi=dpi,
            facecolor=CORES.get("graficoFundo", CORES["superficie"]),
        )
        eixo = figura.add_subplot(111)

        posicoes = np.asarray(posicoes_x, dtype=float)
        xlim, ylim = calcular_limites_eixo_agora(
            posicoes,
            valores,
            preco_fechamento_anterior=resumo.fechamento_anterior,
        )
        cor = obter_cor_tendencia_agora(resumo.fechamento, resumo.fechamento_anterior)
        linha = desenhar_serie_agora(
            eixo,
            posicoes,
            valores,
            pontos_tooltip,
            modelo=self._modelo_grafico,
            cor=cor,
            y_base=ylim[0],
        )
        desenhar_linha_fechamento_anterior(eixo, resumo.fechamento_anterior, resumo.moeda, xlim)
        configurar_eixo_intraday_agora(eixo, xlim, ylim)
        titulo = (
            f"Intraday — {codigo_exibicao(self._simbolo)} "
            f"({formatar_data_ptbr(self._data_ref)})"
        )
        finalizar_figura_grafico(eixo, figura, titulo)

        canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)
        configurar_tooltip_acao(
            canvas,
            eixo,
            linha,
            pontos_tooltip,
            self._simbolo,
            resumo.moeda,
            somente_horario=True,
        )
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        self._figura = figura
        self._canvas = canvas
        self._eixo = eixo
        self._controle_zoom = criar_controle_zoom(canvas, eixo)
        montar_botoes_zoom_grafico(self._barra_zoom, lambda: self._controle_zoom)


def abrir_grafico_agora_dia(
    pai: ctk.CTk,
    simbolo: str,
    data_ref: date,
    *,
    linha_carteira: object | None = None,
) -> JanelaGraficoAgoraDia | None:
    if not pai.winfo_exists():
        return None
    return JanelaGraficoAgoraDia(pai, simbolo, data_ref)
