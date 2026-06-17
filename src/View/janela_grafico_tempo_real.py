"""Janela de grafico intraday com atualizacao automatica (tempo quase real)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Tool.cotacao_dual_helper import codigo_exibicao, rotulo_tipo_ativo
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread, janela_ui_ainda_ativa
from src.View.destaque_cotacao_helper import buscar_cotacao_com_cambio
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.grafico_helper import aplicar_tema_matplotlib, configurar_rotulos_eixo_x, configurar_tooltip_acao
from src.View.tema import CORES

INTERVALO_ATUALIZACAO_MS = 5_000
ALTURA_GRAFICO_PX = 520


class JanelaGraficoTempoReal(ctk.CTkToplevel):
    """Acompanha o ativo no dia com cotacao e grafico atualizados automaticamente."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: Any,
        simbolo: str,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._simbolo = simbolo
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._eixo = None
        self._linha_grafico = None
        self._area_grafico = None
        self._job_atualizacao: str | None = None
        self._ao_vivo = True
        self._carregando = False
        self._periodo_usado = "agora"

        codigo = codigo_exibicao(simbolo)
        self.title(f"Agora — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 650)

        self._montar_interface()
        configurar_janela_maximizada(
            self,
            ao_apos_layout=self._ajustar_grafico_ao_redimensionar,
            janela_pai=pai,
        )
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(400, self._atualizar_dados)
        self._agendar_proxima_atualizacao()

    def _ao_fechar(self) -> None:
        self._ao_vivo = False
        if self._job_atualizacao is not None:
            try:
                self.after_cancel(self._job_atualizacao)
            except Exception:
                pass
            self._job_atualizacao = None
        if self._figura is not None:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
        self.destroy()

    def _montar_interface(self) -> None:
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=16, pady=(0, 12))

        self._label_rodape = ctk.CTkLabel(
            rodape,
            text="Atualizacao automatica a cada 5 segundos. Dados via Yahoo Finance (podem ter atraso de mercado).",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            anchor="w",
        )
        self._label_rodape.pack(side="left", fill="x", expand=True)

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

        barra_topo = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_topo.pack(fill="x", padx=16, pady=(12, 4))

        codigo = codigo_exibicao(self._simbolo)
        tipo = rotulo_tipo_ativo(self._simbolo)
        ctk.CTkLabel(
            barra_topo,
            text=f"{codigo}  ·  {tipo}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")

        self._badge_ao_vivo = ctk.CTkLabel(
            barra_topo,
            text="AO VIVO",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            fg_color=CORES["erro"],
            corner_radius=6,
            width=72,
            height=26,
        )
        self._badge_ao_vivo.pack(side="left", padx=(12, 0))

        self._btn_pausar = ctk.CTkButton(
            barra_topo,
            text="Pausar",
            command=self._alternar_pausa,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=90,
        )
        self._btn_pausar.pack(side="right")

        ctk.CTkButton(
            barra_topo,
            text="Atualizar agora",
            command=self._atualizar_dados,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=130,
        ).pack(side="right", padx=(0, 8))

        painel_preco = ctk.CTkFrame(
            cabecalho,
            fg_color=CORES.get("infoFundo", CORES["fundo"]),
            corner_radius=10,
            border_width=2,
            border_color=CORES["primaria"],
        )
        painel_preco.pack(fill="x", padx=16, pady=(4, 8))

        self._label_preco = ctk.CTkLabel(
            painel_preco,
            text="—",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=CORES["texto"],
        )
        self._label_preco.pack(anchor="w", padx=16, pady=(10, 0))

        self._label_variacao = ctk.CTkLabel(
            painel_preco,
            text="Carregando...",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["textoSecundario"],
        )
        self._label_variacao.pack(anchor="w", padx=16, pady=(0, 4))

        self._label_detalhes = ctk.CTkLabel(
            painel_preco,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            justify="left",
        )
        self._label_detalhes.pack(anchor="w", padx=16, pady=(0, 10))

        self._label_status = ctk.CTkLabel(
            cabecalho,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(anchor="w", padx=16, pady=(0, 10))

        self._frame_grafico = ctk.CTkFrame(
            self,
            fg_color=CORES["superficie"],
            corner_radius=12,
            height=ALTURA_GRAFICO_PX,
        )
        self._frame_grafico.pack(fill="both", expand=True, padx=16, pady=(8, 8))
        self._frame_grafico.pack_propagate(False)

    def _alternar_pausa(self) -> None:
        self._ao_vivo = not self._ao_vivo
        if self._ao_vivo:
            self._btn_pausar.configure(text="Pausar")
            self._badge_ao_vivo.configure(fg_color=CORES["erro"], text="AO VIVO")
            self._agendar_proxima_atualizacao()
        else:
            self._btn_pausar.configure(text="Retomar")
            self._badge_ao_vivo.configure(fg_color=CORES["textoSecundario"], text="PAUSADO")
            if self._job_atualizacao is not None:
                try:
                    self.after_cancel(self._job_atualizacao)
                except Exception:
                    pass
                self._job_atualizacao = None

    def _agendar_proxima_atualizacao(self) -> None:
        if not self._ao_vivo or not janela_ui_ainda_ativa(self):
            return
        self._job_atualizacao = self.after(INTERVALO_ATUALIZACAO_MS, self._ciclo_automatico)

    def _ciclo_automatico(self) -> None:
        self._job_atualizacao = None
        if not self._ao_vivo or not janela_ui_ainda_ativa(self):
            return
        self._atualizar_dados()
        self._agendar_proxima_atualizacao()

    def _atualizar_dados(self) -> None:
        if self._carregando or not janela_ui_ainda_ativa(self):
            return
        self._carregando = True
        self._label_status.configure(text="Atualizando cotacao e grafico...")

        def buscar():
            cotacao_dados = buscar_cotacao_com_cambio(self._controlador, self._simbolo)
            serie, erro = self._controlador.obter_historico(self._simbolo, "agora")
            periodo = "agora"
            if erro or serie is None:
                serie, erro = self._controlador.obter_historico(self._simbolo, "dia")
                periodo = "dia"
            return cotacao_dados, serie, erro, periodo

        def ao_concluir(resultado, erro_thread):
            self._carregando = False
            if not janela_ui_ainda_ativa(self):
                return
            if erro_thread:
                self._label_status.configure(text=f"Erro: {erro_thread}", text_color=CORES["erro"])
                return

            cotacao_dados, serie, erro_hist, periodo = resultado
            self._periodo_usado = periodo
            self._atualizar_painel_preco(cotacao_dados)

            if erro_hist or serie is None or not getattr(serie, "pontos", None):
                self._label_status.configure(
                    text=erro_hist or "Grafico intraday indisponivel.",
                    text_color=CORES["erro"],
                )
                return

            pontos = serie.pontos
            labels = [p.data_exibicao for p in pontos]
            valores = [p.preco_fechamento for p in pontos]
            moeda = cotacao_dados[0].moeda if cotacao_dados[0] else "BRL"
            intervalo = "1 min" if periodo == "agora" else "5 min"
            titulo = f"Intraday — {codigo_exibicao(self._simbolo)} ({intervalo})"
            pontos_tooltip = [
                {
                    "data": p.data_exibicao,
                    "preco": p.preco_fechamento,
                    "volume": p.volume,
                }
                for p in pontos
            ]
            self._desenhar_grafico(labels, valores, titulo, self._simbolo, moeda, pontos_tooltip)

            agora = datetime.now().strftime("%H:%M:%S")
            self._label_status.configure(
                text=f"Ultima atualizacao as {agora} · intervalo {intervalo} · {len(pontos)} pontos",
                text_color=CORES["textoSecundario"],
            )

        executar_em_thread(self, buscar, ao_concluir)

    def _atualizar_painel_preco(self, cotacao_dados: tuple) -> None:
        cotacao, taxa, aviso = cotacao_dados
        if cotacao is None:
            self._label_preco.configure(text="—")
            self._label_variacao.configure(text=aviso or "Cotacao indisponivel", text_color=CORES["erro"])
            self._label_detalhes.configure(text="")
            return

        moeda = cotacao.moeda or "BRL"
        self._label_preco.configure(text=formatar_moeda(cotacao.preco, moeda))

        cor_var = CORES["sucesso"] if cotacao.variacao_percentual >= 0 else CORES["erro"]
        self._label_variacao.configure(
            text=formatar_variacao(cotacao.variacao_valor, cotacao.variacao_percentual, moeda),
            text_color=cor_var,
        )

        detalhes = [cotacao.nome or codigo_exibicao(cotacao.simbolo)]
        if cotacao.volume is not None:
            detalhes.append(f"Volume: {cotacao.volume:,}".replace(",", "."))
        if taxa:
            detalhes.append(f"US$ 1 = {formatar_moeda(taxa, 'BRL')}")
        if aviso:
            detalhes.append(aviso)
        self._label_detalhes.configure(text="  ·  ".join(detalhes))

    def _desenhar_grafico(
        self,
        labels: list[str],
        valores: list[float],
        titulo: str,
        simbolo: str,
        moeda: str,
        pontos_tooltip: list[dict],
    ) -> None:
        if not valores:
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
        self._eixo = None
        self._linha_grafico = None

        largura_px = max(500, self._frame_grafico.winfo_width() - 16)
        altura_px = max(400, ALTURA_GRAFICO_PX - 16)
        dpi = 100
        figura = Figure(
            figsize=(largura_px / dpi, altura_px / dpi),
            dpi=dpi,
            facecolor=CORES.get("graficoFundo", CORES["superficie"]),
        )
        eixo = figura.add_subplot(111)
        indices = np.arange(len(valores))
        cor_linha = CORES["primaria"]

        eixo.fill_between(indices, valores, alpha=0.18, color=cor_linha)
        linha, = eixo.plot(indices, valores, color=cor_linha, linewidth=2)
        eixo.set_title(titulo, fontsize=14, fontweight="bold")
        eixo.set_ylabel("Preco", fontsize=11)
        configurar_rotulos_eixo_x(eixo, labels, max_rotulos=12)
        eixo.grid(True, alpha=0.25, color=CORES["borda"])
        aplicar_tema_matplotlib(eixo, figura)
        figura.subplots_adjust(bottom=0.18, left=0.07, right=0.98, top=0.92)

        canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)
        configurar_tooltip_acao(canvas, eixo, linha, pontos_tooltip, simbolo, moeda)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        self._figura = figura
        self._canvas = canvas
        self._eixo = eixo
        self._linha_grafico = linha
        self.after(80, lambda: self._ajustar_grafico_ao_redimensionar(0))

    def _ajustar_grafico_ao_redimensionar(self, tentativa: int = 0) -> None:
        if self._canvas is None or self._figura is None:
            if tentativa < 30:
                self.after(100, lambda: self._ajustar_grafico_ao_redimensionar(tentativa + 1))
            return
        try:
            self._frame_grafico.update_idletasks()
            largura_px = max(500, self._frame_grafico.winfo_width() - 16)
            altura_px = max(400, self._frame_grafico.winfo_height() - 16)
            if largura_px < 520 and tentativa < 30:
                self.after(100, lambda: self._ajustar_grafico_ao_redimensionar(tentativa + 1))
                return
            dpi = self._figura.get_dpi()
            self._figura.set_size_inches(largura_px / dpi, altura_px / dpi, forward=True)
            self._canvas.draw_idle()
        except Exception:
            pass


def abrir_grafico_tempo_real(pai: ctk.CTk, controlador: Any, simbolo: str) -> JanelaGraficoTempoReal | None:
    """Abre a tela Agora para acompanhar o ativo em tempo quase real."""
    if not pai.winfo_exists():
        return None
    return JanelaGraficoTempoReal(pai, controlador, simbolo)
