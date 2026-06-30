"""Grafico intraday do ativo na Nasdaq (ticker nos EUA) com opcao de impressao."""
from __future__ import annotations

from datetime import date, datetime

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.View import mensagem_helper as messagebox

from src.Controller.controlador_mercado import ControladorMercado
from src.Service.agora_historico_dia_servico import data_padrao_consulta_agora
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.dia_util_helper import eh_dia_util, formatar_data_ptbr
from src.Tool.grafico_impressao_helper import imprimir_figura_grafico, salvar_figura_grafico
from src.Tool.intraday_agora_helper import calcular_atraso_candles_minutos, completar_serie_intraday_com_cotacao
from src.Tool.janela_helper import (
    configurar_janela_maximizada,
    executar_em_thread,
    janela_ui_ainda_ativa,
)
from src.Tool.nasdaq_ticker_helper import resolver_ticker_nasdaq
from src.View.campo_data_calendario_helper import montar_campo_data_calendario
from src.View.destaque_cotacao_helper import buscar_cotacao_com_cambio
from src.View.formatadores import formatar_moeda, formatar_variacao_com_rotulo
from src.View.grafico_agora_helper import (
    calcular_preco_fechamento_anterior,
    criar_subplots_agora,
    desenhar_linha_fechamento_anterior,
    desenhar_serie_agora,
    desenhar_volume_agora,
    finalizar_figura_grafico_agora,
    obter_cor_tendencia_agora,
    ocultar_rotulos_eixo_x_preco,
)
from src.View.grafico_helper import configurar_tooltip_acao, extrair_minutos_dia_de_ponto
from src.View.grafico_marcador_cruz_helper import reaplicar_marcador_cruz_canvas
from src.View.grafico_modelo_helper import ModeloGrafico, montar_seletor_modelo_grafico
from src.View.grafico_nasdaq_helper import (
    calcular_limites_eixo_nasdaq,
    configurar_eixo_intraday_nasdaq,
)
from src.View.grafico_zoom_helper import criar_controle_zoom, montar_botoes_zoom_grafico
from src.View.janela_grafico_agora_dia import abrir_grafico_agora_dia
from src.View.janela_negocios_agora import JanelaNegociosAgora, abrir_janela_negocios_agora
from src.View.janela_resumo_semana_agora import (
    JanelaResumoSemanaAgora,
    abrir_janela_resumo_semana_agora,
)
from src.View.tema import CORES

_INTERVALO_ATUALIZACAO_MS = 5_000
_ALTURA_GRAFICO_MIN_PX = 360


class JanelaGraficoNasdaqAgora(ctk.CTkToplevel):
    """Intraday do ticker nos EUA correspondente ao ativo da tela Agora."""

    def __init__(
        self,
        pai: ctk.CTkToplevel,
        simbolo_origem: str,
        ticker_nasdaq: str,
    ) -> None:
        super().__init__(pai)
        self._pai_agora = pai
        self._simbolo_origem = simbolo_origem
        self._ticker_nasdaq = ticker_nasdaq
        self._controlador = ControladorMercado()
        self._modelo_grafico: ModeloGrafico = "area"
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._eixo = None
        self._eixo_volume = None
        self._controle_zoom = None
        self._carregando = False
        self._ao_vivo = True
        self._job_atualizacao: str | None = None
        self._janela_negocios: JanelaNegociosAgora | None = None
        self._janela_resumo_semana: JanelaResumoSemanaAgora | None = None

        codigo_b3 = codigo_exibicao(simbolo_origem)
        self.title(f"Nasdaq — {ticker_nasdaq} ({codigo_b3})")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(920, 640)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(300, self._atualizar_dados)
        self._agendar_proxima_atualizacao()

    def _montar_interface(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.grid(row=0, column=0, sticky="ew")

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            barra,
            text=f"Nasdaq — {self._ticker_nasdaq}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")

        ctk.CTkLabel(
            barra,
            text=f"  ·  Origem: {codigo_exibicao(self._simbolo_origem)}",
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
        ).pack(side="left")

        frame_acoes = ctk.CTkFrame(barra, fg_color="transparent")
        frame_acoes.pack(side="right")

        ctk.CTkButton(
            frame_acoes,
            text="Atualizar",
            command=self._atualizar_dados,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=100,
        ).pack(side="right")

        ctk.CTkButton(
            frame_acoes,
            text="Imprimir",
            command=self._imprimir_grafico,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=100,
        ).pack(side="right", padx=(0, 8))

        ctk.CTkButton(
            frame_acoes,
            text="Salvar imagem",
            command=self._salvar_grafico,
            fg_color=CORES["zebraEscura"],
            hover_color=CORES["borda"],
            text_color=CORES["texto"],
            width=120,
        ).pack(side="right", padx=(0, 8))

        barra_modelo = ctk.CTkFrame(frame_acoes, fg_color="transparent")
        barra_modelo.pack(side="right", padx=(0, 12))
        montar_seletor_modelo_grafico(
            barra_modelo,
            modelo_inicial=self._modelo_grafico,
            ao_mudar=self._alternar_modelo_grafico,
            largura_combo=110,
        )

        barra_dia = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_dia.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            barra_dia,
            text="Dia:",
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
        ).pack(side="left", padx=(0, 6))

        self._campo_data_dia = montar_campo_data_calendario(
            barra_dia,
            valor_inicial=data_padrao_consulta_agora(),
            largura_entrada=108,
        )

        ctk.CTkButton(
            barra_dia,
            text="Ver dia",
            command=self._abrir_tela_dia_historico,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=88,
            height=28,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            barra_dia,
            text="Negocios",
            command=self._abrir_negocios,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=96,
            height=28,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            barra_dia,
            text="Resumo do mês",
            command=self._abrir_resumo_semana,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=148,
            height=28,
        ).pack(side="left", padx=(8, 0))

        painel_preco = ctk.CTkFrame(
            cabecalho,
            fg_color=CORES.get("infoFundo", CORES["fundo"]),
            corner_radius=10,
            border_width=2,
            border_color=CORES["primaria"],
        )
        painel_preco.pack(fill="x", padx=16, pady=(0, 8))

        linha_preco = ctk.CTkFrame(painel_preco, fg_color="transparent")
        linha_preco.pack(fill="x", padx=16, pady=10)

        self._label_preco = ctk.CTkLabel(
            linha_preco,
            text="—",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color=CORES["texto"],
        )
        self._label_preco.pack(side="left", anchor="s")

        self._label_variacao = ctk.CTkLabel(
            linha_preco,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["textoSecundario"],
        )
        self._label_variacao.pack(side="left", anchor="s", padx=(16, 0), pady=(8, 0))

        self._label_status = ctk.CTkLabel(
            cabecalho,
            text="Carregando grafico Nasdaq...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            anchor="w",
            wraplength=900,
            justify="left",
        )
        self._label_status.pack(fill="x", padx=16, pady=(0, 10))

        corpo = ctk.CTkFrame(self, fg_color=CORES["fundo"])
        corpo.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        corpo.grid_rowconfigure(1, weight=1)
        corpo.grid_columnconfigure(0, weight=1)

        self._barra_zoom = ctk.CTkFrame(corpo, fg_color="transparent")
        self._barra_zoom.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        montar_botoes_zoom_grafico(self._barra_zoom, lambda: self._controle_zoom)

        self._frame_grafico = ctk.CTkFrame(corpo, fg_color="transparent")
        self._frame_grafico.grid(row=1, column=0, sticky="nsew")

    def _ao_fechar(self) -> None:
        self._ao_vivo = False
        if self._janela_negocios is not None:
            try:
                if self._janela_negocios.winfo_exists():
                    self._janela_negocios._ao_fechar()
            except Exception:
                pass
            self._janela_negocios = None
        if self._janela_resumo_semana is not None:
            try:
                if self._janela_resumo_semana.winfo_exists():
                    self._janela_resumo_semana._ao_fechar()
            except Exception:
                pass
            self._janela_resumo_semana = None
        if self._job_atualizacao is not None:
            try:
                self.after_cancel(self._job_atualizacao)
            except Exception:
                pass
        if self._figura is not None:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
        self.destroy()

    def _agendar_proxima_atualizacao(self) -> None:
        if not self._ao_vivo:
            return
        self._job_atualizacao = self.after(_INTERVALO_ATUALIZACAO_MS, self._ciclo_automatico)

    def _ciclo_automatico(self) -> None:
        self._job_atualizacao = None
        if not self._ao_vivo or not janela_ui_ainda_ativa(self):
            return
        self._atualizar_dados()
        self._agendar_proxima_atualizacao()

    def _alternar_modelo_grafico(self, modelo: ModeloGrafico) -> None:
        self._modelo_grafico = modelo
        self._atualizar_dados()

    def _abrir_tela_dia_historico(self) -> None:
        data_ref, erro = self._campo_data_dia.obter_data()
        if erro or data_ref is None:
            messagebox.showerror(
                "Data invalida",
                erro or "Informe a data no formato dd/mm/aaaa.",
                parent=self,
            )
            return

        hoje = date.today()
        if data_ref > hoje:
            messagebox.showerror(
                "Data invalida",
                "A data nao pode ser futura.",
                parent=self,
            )
            return

        if not eh_dia_util(data_ref):
            if not messagebox.askyesno(
                "Dia nao util",
                f"{formatar_data_ptbr(data_ref)} e fim de semana. Deseja consultar mesmo assim?",
                parent=self,
            ):
                return

        abrir_grafico_agora_dia(self, self._ticker_nasdaq, data_ref)

    def _abrir_negocios(self) -> None:
        self._janela_negocios = abrir_janela_negocios_agora(
            self,
            self._ticker_nasdaq,
            janela_atual=self._janela_negocios,
        )

    def _abrir_resumo_semana(self) -> None:
        self._janela_resumo_semana = abrir_janela_resumo_semana_agora(
            self,
            self._ticker_nasdaq,
            janela_atual=self._janela_resumo_semana,
        )

    def _imprimir_grafico(self) -> None:
        if self._figura is None:
            messagebox.showwarning(
                "Imprimir",
                "Aguarde o grafico carregar antes de imprimir.",
                parent=self,
            )
            return
        if not imprimir_figura_grafico(self._figura, janela_pai=self):
            messagebox.showerror(
                "Imprimir",
                "Nao foi possivel enviar o grafico para a impressora.",
                parent=self,
            )

    def _salvar_grafico(self) -> None:
        if self._figura is None:
            messagebox.showwarning(
                "Salvar imagem",
                "Aguarde o grafico carregar antes de salvar.",
                parent=self,
            )
            return
        nome = f"nasdaq-{self._ticker_nasdaq}-{datetime.now().strftime('%Y%m%d-%H%M')}.png"
        if salvar_figura_grafico(self._figura, nome, janela_pai=self):
            messagebox.showinfo("Salvar imagem", "Grafico salvo com sucesso.", parent=self)

    def _atualizar_dados(self) -> None:
        if self._carregando or not janela_ui_ainda_ativa(self):
            return
        self._carregando = True
        self._label_status.configure(text="Atualizando cotacao Nasdaq...")

        def buscar():
            cotacao_dados = buscar_cotacao_com_cambio(self._controlador, self._ticker_nasdaq)
            serie, erro = self._controlador.obter_historico(self._ticker_nasdaq, "agora")
            periodo = "agora"
            if erro or serie is None:
                serie, erro = self._controlador.obter_historico(self._ticker_nasdaq, "dia")
                periodo = "dia"
            return cotacao_dados, serie, erro, periodo

        def ao_concluir(resultado, erro_thread):
            self._carregando = False
            if not janela_ui_ainda_ativa(self):
                return
            if erro_thread:
                self._label_status.configure(text=erro_thread, text_color=CORES["erro"])
                return
            if resultado is None:
                self._label_status.configure(
                    text="Nao foi possivel carregar os dados da Nasdaq.",
                    text_color=CORES["erro"],
                )
                return

            cotacao_dados, serie, erro_hist, periodo = resultado
            self._atualizar_painel_preco(cotacao_dados)

            if erro_hist or serie is None or not getattr(serie, "pontos", None):
                self._label_status.configure(
                    text=erro_hist or "Grafico intraday indisponivel na Nasdaq.",
                    text_color=CORES["erro"],
                )
                return

            cotacao_viva = cotacao_dados[0] if cotacao_dados else None
            preco_vivo = cotacao_viva.preco if cotacao_viva else None
            pontos = (
                completar_serie_intraday_com_cotacao(serie.pontos, preco_vivo)
                if periodo == "agora"
                else serie.pontos
            )
            posicoes_x, valores, pontos_tooltip = self._montar_serie_intraday(pontos)
            if not valores:
                self._label_status.configure(
                    text="Grafico indisponivel (horarios invalidos).",
                    text_color=CORES["erro"],
                )
                return

            moeda = "USD"
            preco_fechamento_anterior = None
            if cotacao_viva is not None:
                preco_fechamento_anterior = calcular_preco_fechamento_anterior(
                    cotacao_viva.preco,
                    cotacao_viva.variacao_valor,
                )

            self._desenhar_grafico(
                posicoes_x,
                valores,
                pontos_tooltip,
                moeda=moeda,
                preco_fechamento_anterior=preco_fechamento_anterior,
                periodo=periodo,
                pontos_originais=serie.pontos,
                preco_vivo=preco_vivo,
            )

        executar_em_thread(self, buscar, ao_concluir)

    def _atualizar_painel_preco(self, cotacao_dados) -> None:
        cotacao = cotacao_dados[0] if cotacao_dados else None
        if cotacao is None:
            self._label_preco.configure(text="—")
            self._label_variacao.configure(text="Cotacao indisponivel", text_color=CORES["erro"])
            return

        moeda = cotacao.moeda or "USD"
        self._label_preco.configure(text=formatar_moeda(cotacao.preco, moeda))
        cor = CORES["sucesso"] if cotacao.variacao_percentual >= 0 else CORES["erro"]
        self._label_variacao.configure(
            text=formatar_variacao_com_rotulo(
                cotacao.variacao_valor,
                cotacao.variacao_percentual,
                "Variacao do dia",
                moeda,
            ),
            text_color=cor,
        )

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

    def _desenhar_grafico(
        self,
        posicoes_x: list[float],
        valores: list[float],
        pontos_tooltip: list[dict],
        *,
        moeda: str,
        preco_fechamento_anterior: float | None,
        periodo: str,
        pontos_originais: list,
        preco_vivo: float | None,
    ) -> None:
        xlim_antigo = self._eixo.get_xlim() if self._eixo is not None else None
        ylim_antigo = self._eixo.get_ylim() if self._eixo is not None else None
        preservar_zoom = (
            self._controle_zoom is not None
            and self._controle_zoom._esta_ampliado()
        )

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
        eixo, eixo_volume = criar_subplots_agora(figura)

        posicoes = np.asarray(posicoes_x, dtype=float)
        xlim, ylim = calcular_limites_eixo_nasdaq(
            posicoes,
            valores,
            preco_fechamento_anterior=preco_fechamento_anterior,
        )
        if preservar_zoom and xlim_antigo and ylim_antigo:
            xlim, ylim = xlim_antigo, ylim_antigo

        cor = obter_cor_tendencia_agora(
            valores[-1] if valores else None,
            preco_fechamento_anterior,
        )
        linha = desenhar_serie_agora(
            eixo,
            posicoes,
            valores,
            pontos_tooltip,
            modelo=self._modelo_grafico,
            cor=cor,
            y_base=ylim[0],
        )
        desenhar_linha_fechamento_anterior(eixo, preco_fechamento_anterior, moeda, xlim)
        configurar_eixo_intraday_nasdaq(eixo, xlim, ylim)
        ocultar_rotulos_eixo_x_preco(eixo)
        desenhar_volume_agora(eixo_volume, figura, posicoes, pontos_tooltip, xlim)
        titulo = f"Nasdaq — {self._ticker_nasdaq} (intraday)"
        finalizar_figura_grafico_agora(eixo, figura, titulo, com_painel_volume=True)

        canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)
        configurar_tooltip_acao(
            canvas,
            eixo,
            linha,
            pontos_tooltip,
            self._ticker_nasdaq,
            moeda,
            somente_horario=True,
            eixo_volume=eixo_volume,
        )
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        self._figura = figura
        self._canvas = canvas
        self._eixo = eixo
        self._eixo_volume = eixo_volume
        self._controle_zoom = criar_controle_zoom(canvas, eixo, eixo_volume=eixo_volume)
        reaplicar_marcador_cruz_canvas(canvas, eixo, eixo_volume=eixo_volume)

        intervalo = "1 min" if periodo == "agora" else "5 min"
        atraso = calcular_atraso_candles_minutos(pontos_originais) if periodo == "agora" else None
        hora = datetime.now().strftime("%H:%M:%S")
        status = (
            f"Ultima atualizacao as {hora} · {self._ticker_nasdaq} · "
            f"intervalo {intervalo} · {len(pontos_tooltip)} pontos"
        )
        if periodo == "agora" and atraso and atraso >= 2:
            status += f" · candles ~{atraso} min atrasados · preco ao vivo ate agora"
        self._label_status.configure(text=status, text_color=CORES["textoSecundario"])


def abrir_janela_grafico_nasdaq_agora(
    pai: ctk.CTkToplevel,
    simbolo_origem: str,
    *,
    janela_atual: JanelaGraficoNasdaqAgora | None = None,
) -> JanelaGraficoNasdaqAgora | None:
    """Abre ou foca o grafico Nasdaq do ativo exibido na tela Agora."""
    ticker, erro = resolver_ticker_nasdaq(simbolo_origem)
    if erro or not ticker:
        messagebox.showerror("Nasdaq", erro or "Ticker indisponivel.", parent=pai)
        return None

    if janela_atual is not None:
        try:
            if janela_atual.winfo_exists():
                if janela_atual._ticker_nasdaq == ticker:
                    janela_atual.focus_force()
                    janela_atual.lift()
                    janela_atual._atualizar_dados()
                    return janela_atual
                janela_atual._ao_fechar()
        except Exception:
            pass

    return JanelaGraficoNasdaqAgora(pai, simbolo_origem, ticker)
