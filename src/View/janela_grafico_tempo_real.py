"""Janela de grafico intraday com atualizacao automatica (tempo quase real)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any
import time

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Model.carteira import LinhaCarteira
from src.Service.agora_historico_dia_servico import data_padrao_consulta_agora
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.cotacao_dual_helper import codigo_exibicao, rotulo_tipo_ativo
from src.Service.carteira_servico import CarteiraServico
from src.Tool.dia_util_helper import eh_dia_util, formatar_data_ptbr
from src.Tool.intraday_agora_helper import (
    calcular_atraso_candles_minutos,
    completar_serie_intraday_com_cotacao,
)
from src.Tool.janela_helper import (
    ajustar_janela_area_trabalho,
    configurar_janela_maximizada,
    executar_em_thread,
    janela_ui_ainda_ativa,
)
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr, formatar_centavos_ptbr
from src.Tool.projecao_intraday_agora_helper import calcular_projecao_fim_dia
from src.Service.agora_metricas_mercado_servico import AgoraMetricasMercadoServico, MetricasMercadoAgora
from src.View.agora_carteira_helper import ResumoCarteiraAgora, buscar_resumo_carteira
from src.View.campo_data_calendario_helper import montar_campo_data_calendario
from src.View.janela_grafico_agora_dia import abrir_grafico_agora_dia
from src.View.janela_negocios_agora import JanelaNegociosAgora, abrir_janela_negocios_agora
from src.View.janela_resumo_semana_agora import (
    JanelaResumoSemanaAgora,
    abrir_janela_resumo_semana_agora,
)
from src.View import mensagem_helper as messagebox
from src.View.agora_painel_metricas_helper import PainelMetricasAgora
from src.View.destaque_cotacao_helper import buscar_cotacao_com_cambio
from src.View.formatadores import formatar_moeda, formatar_variacao_com_rotulo
from src.View.grafico_agora_helper import (
    calcular_limites_eixo_agora,
    calcular_preco_fechamento_anterior,
    configurar_eixo_intraday_agora,
    desenhar_linha_fechamento_anterior,
    desenhar_projecao_fim_dia_agora,
    desenhar_serie_agora,
    obter_cor_tendencia_agora,
)
from src.View.grafico_helper import (
    configurar_tooltip_acao,
    extrair_minutos_dia_de_ponto,
    finalizar_figura_grafico,
)
from src.View.grafico_modelo_helper import (
    ModeloGrafico,
    montar_seletor_modelo_grafico,
)
from src.View.grafico_zoom_helper import criar_controle_zoom, montar_botoes_zoom_grafico
from src.View.tabela_carteira_helper import _formatar_quantidade
from src.View.tema import CORES

INTERVALO_ATUALIZACAO_MS = 5_000
INTERVALO_METRICAS_MS = 60_000
ALTURA_GRAFICO_MINIMA_PX = 280
_ALTURA_INFO_ROLAGEM_PX = 220
_FONTE_BANNER_ALERTA = 39  # 3x do tamanho base — apenas mensagem VENDER/COMPRAR


class JanelaGraficoTempoReal(ctk.CTkToplevel):
    """Acompanha o ativo no dia com cotacao e grafico atualizados automaticamente."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: Any,
        simbolo: str,
        linha_carteira: LinhaCarteira | None = None,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._simbolo = simbolo
        self._linha_carteira = linha_carteira
        self._config_painel = ConfigPainelIni()
        self._resumo_carteira: ResumoCarteiraAgora | None = buscar_resumo_carteira(
            simbolo,
            linha_carteira,
        )
        self._alerta_preco_venda_limite: float | None = self._config_painel.carregar_alerta_preco_venda_agora(
            simbolo
        )
        self._alerta_compra_limite: float | None = self._config_painel.carregar_alerta_compra_acao(
            simbolo
        )
        self._alerta_venda_ativo = False
        self._alerta_compra_ativo = False
        self._preco_atual_cotacao: float | None = None
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._eixo = None
        self._linha_grafico = None
        self._controle_zoom = None
        self._area_grafico = None
        self._job_atualizacao: str | None = None
        self._ao_vivo = True
        self._carregando = False
        self._periodo_usado = "agora"
        self._modelo_grafico: ModeloGrafico = "area"
        self._dados_grafico_atual: dict | None = None
        self._servico_metricas = AgoraMetricasMercadoServico()
        self._painel_metricas: PainelMetricasAgora | None = None
        self._ultima_busca_metricas_ms = 0
        self._preco_referencia_5_dias: float | None = None
        self._editando_alerta = False
        self._bloqueio_foco_alerta = False
        self._job_redimensionar_grafico: str | None = None
        self._janela_negocios: JanelaNegociosAgora | None = None
        self._janela_resumo_semana: JanelaResumoSemanaAgora | None = None

        codigo = codigo_exibicao(simbolo)
        self.title(f"Agora — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 650)

        self._montar_interface()
        configurar_janela_maximizada(
            self,
            ao_apos_layout=self._ao_layout_inicial,
            janela_pai=pai,
        )
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(400, lambda: self._atualizar_dados(forcar_metricas=True))
        self._agendar_proxima_atualizacao()

    def _ao_fechar(self) -> None:
        self._ao_vivo = False
        if self._job_redimensionar_grafico is not None:
            try:
                self.after_cancel(self._job_redimensionar_grafico)
            except Exception:
                pass
            self._job_redimensionar_grafico = None
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
        self.grid_rowconfigure(2, weight=1, minsize=ALTURA_GRAFICO_MINIMA_PX)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.grid(row=0, column=0, sticky="ew")

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

        barra_dia = ctk.CTkFrame(barra_topo, fg_color="transparent")
        barra_dia.pack(side="left", padx=(16, 0))

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

        barra_modelo = ctk.CTkFrame(barra_topo, fg_color="transparent")
        barra_modelo.pack(side="right", padx=(0, 12))
        montar_seletor_modelo_grafico(
            barra_modelo,
            modelo_inicial=self._modelo_grafico,
            ao_mudar=self._alternar_modelo_grafico,
            largura_combo=110,
        )

        ctk.CTkButton(
            barra_topo,
            text="Atualizar agora",
            command=lambda: self._atualizar_dados(forcar_metricas=True),
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

        self._label_variacao_compra = ctk.CTkLabel(
            self._frame_indicadores,
            text="",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=CORES["textoSecundario"],
            anchor="w",
        )
        self._label_variacao_compra.pack(anchor="w", pady=(4, 0))

        self._frame_alerta_topo = ctk.CTkFrame(
            linha_preco,
            fg_color=CORES["superficie"],
            corner_radius=8,
            border_width=2,
            border_color=CORES["primaria"],
        )
        self._frame_alerta_topo.pack(side="right", fill="both", expand=True, padx=(20, 0), pady=(0, 2))

        self._frame_alerta_topo_venda = ctk.CTkFrame(self._frame_alerta_topo, fg_color="transparent")
        self._montar_alerta_topo_venda(self._frame_alerta_topo_venda)

        self._frame_alerta_topo_compra = ctk.CTkFrame(self._frame_alerta_topo, fg_color="transparent")
        self._montar_alerta_topo_compra(self._frame_alerta_topo_compra)

        self._label_alerta_venda = ctk.CTkLabel(
            painel_preco,
            text="",
            font=ctk.CTkFont(size=_FONTE_BANNER_ALERTA, weight="bold"),
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            fg_color=CORES["erro"],
            corner_radius=8,
            anchor="w",
            justify="left",
            wraplength=1200,
        )
        self._label_alerta_venda.pack(fill="x", padx=16, pady=(8, 10))
        self._label_alerta_venda.pack_forget()

        self._label_alerta_compra = ctk.CTkLabel(
            painel_preco,
            text="",
            font=ctk.CTkFont(size=_FONTE_BANNER_ALERTA, weight="bold"),
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            fg_color=CORES["sucesso"],
            corner_radius=8,
            anchor="w",
            justify="left",
            wraplength=1200,
        )
        self._label_alerta_compra.pack(fill="x", padx=16, pady=(8, 10))
        self._label_alerta_compra.pack_forget()

        self._label_detalhes = ctk.CTkLabel(
            painel_preco,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            justify="left",
        )
        self._label_detalhes.pack(anchor="w", padx=16, pady=(0, 10))

        self._container_info = ctk.CTkFrame(
            self,
            fg_color=CORES["fundo"],
            height=_ALTURA_INFO_ROLAGEM_PX,
        )
        self._container_info.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        self._container_info.pack_propagate(False)

        self._area_rolagem = ctk.CTkScrollableFrame(
            self._container_info,
            fg_color=CORES["fundo"],
            label_text="",
        )
        self._area_rolagem.pack(fill="both", expand=True)

        self._painel_metricas = PainelMetricasAgora(self._area_rolagem)
        self._painel_metricas.montar().pack(fill="x", pady=(0, 8))

        self._frame_painel_carteira = ctk.CTkFrame(
            self._area_rolagem,
            fg_color=CORES.get("infoFundo", CORES["fundo"]),
            corner_radius=10,
            border_width=1,
            border_color=CORES["borda"],
        )

        titulo_carteira = ctk.CTkLabel(
            self._frame_painel_carteira,
            text="Sua posicao na carteira",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
        )
        titulo_carteira.pack(anchor="w", padx=14, pady=(10, 6))

        grade_carteira = ctk.CTkFrame(self._frame_painel_carteira, fg_color="transparent")
        grade_carteira.pack(fill="x", padx=14, pady=(0, 8))
        for coluna in range(3):
            grade_carteira.grid_columnconfigure(coluna, weight=1)

        def _criar_campo_resumo(coluna: int, rotulo: str) -> ctk.CTkLabel:
            quadro = ctk.CTkFrame(grade_carteira, fg_color=CORES["superficie"], corner_radius=8)
            quadro.grid(row=0, column=coluna, sticky="nsew", padx=(0 if coluna == 0 else 6, 0))
            ctk.CTkLabel(
                quadro,
                text=rotulo,
                font=ctk.CTkFont(size=11),
                text_color=CORES["textoSecundario"],
                anchor="w",
            ).pack(anchor="w", padx=10, pady=(8, 2))
            valor = ctk.CTkLabel(
                quadro,
                text="—",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=CORES["texto"],
                anchor="w",
            )
            valor.pack(anchor="w", padx=10, pady=(0, 8))
            return valor

        self._label_carteira_qtd = _criar_campo_resumo(0, "Quantidade")
        self._label_carteira_compra = _criar_campo_resumo(1, "Preco de compra")
        self._label_carteira_valorizacao = _criar_campo_resumo(2, "Resultado (R$)")

        self._sincronizar_painel_carteira_ou_compra()
        if self._resumo_carteira is not None:
            self._atualizar_campos_carteira(None)

        self._container_grafico = ctk.CTkFrame(self, fg_color="transparent")
        self._container_grafico.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))
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
        montar_botoes_zoom_grafico(self._barra_zoom, lambda: self._controle_zoom)

        self._frame_grafico = ctk.CTkFrame(
            self._container_grafico,
            fg_color=CORES["superficie"],
            corner_radius=12,
        )
        self._frame_grafico.grid(row=2, column=0, sticky="nsew", pady=(0, 4))
        self._frame_grafico.bind("<Configure>", self._ao_configurar_frame_grafico)

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))

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

    def _abrir_tela_dia_historico(self) -> None:
        data_ref, erro = self._campo_data_dia.obter_data()
        if erro or data_ref is None:
            messagebox.showerror("Data invalida", erro or "Informe a data no formato dd/mm/aaaa.", parent=self)
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

        abrir_grafico_agora_dia(
            self,
            self._simbolo,
            data_ref,
            linha_carteira=self._linha_carteira,
        )

    def _abrir_negocios(self) -> None:
        self._janela_negocios = abrir_janela_negocios_agora(
            self,
            self._simbolo,
            janela_atual=self._janela_negocios,
        )

    def _abrir_resumo_semana(self) -> None:
        self._janela_resumo_semana = abrir_janela_resumo_semana_agora(
            self,
            self._simbolo,
            janela_atual=self._janela_resumo_semana,
        )

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

    def _atualizar_dados(self, *, forcar_metricas: bool = False) -> None:
        if self._carregando or not janela_ui_ainda_ativa(self):
            return
        self._carregando = True
        self._label_status.configure(text="Atualizando cotacao e grafico...")
        buscar_metricas = forcar_metricas or self._deve_atualizar_metricas()

        def buscar():
            cotacao_dados = buscar_cotacao_com_cambio(self._controlador, self._simbolo)
            serie, erro = self._controlador.obter_historico(self._simbolo, "agora")
            periodo = "agora"
            if erro or serie is None:
                serie, erro = self._controlador.obter_historico(self._simbolo, "dia")
                periodo = "dia"
            metricas = None
            if buscar_metricas:
                try:
                    metricas = self._servico_metricas.obter_metricas(self._simbolo)
                except Exception:
                    metricas = None
            return cotacao_dados, serie, erro, periodo, metricas

        def ao_concluir(resultado, erro_thread):
            self._carregando = False
            if not janela_ui_ainda_ativa(self):
                return
            estado_foco = self._salvar_estado_foco_alerta()
            entrada_alerta_focada, cursor_alerta = estado_foco
            editando_alerta = entrada_alerta_focada is not None
            self._bloqueio_foco_alerta = True
            self._pausar_mascaras_alerta(True)
            try:
                if erro_thread:
                    self._label_status.configure(text=f"Erro: {erro_thread}", text_color=CORES["erro"])
                    return
                if resultado is None:
                    self._label_status.configure(
                        text="Nao foi possivel carregar os dados.",
                        text_color=CORES["erro"],
                    )
                    return

                try:
                    cotacao_dados, serie, erro_hist, periodo, metricas = resultado
                except (TypeError, ValueError) as exc:
                    self._label_status.configure(
                        text=f"Erro ao processar dados: {exc}",
                        text_color=CORES["erro"],
                    )
                    return

                self._periodo_usado = periodo
                self._atualizar_resumo_carteira()
                self._atualizar_painel_preco(cotacao_dados, atualizar_variacao_5d=not editando_alerta)
                if metricas is not None:
                    self._aplicar_metricas_mercado(
                        metricas,
                        atualizar_variacao_5d=not editando_alerta,
                    )

                if erro_hist or serie is None or not getattr(serie, "pontos", None):
                    self._label_status.configure(
                        text=erro_hist or "Grafico intraday indisponivel.",
                        text_color=CORES["erro"],
                    )
                    return

                pontos_originais = serie.pontos
                cotacao_viva = cotacao_dados[0] if cotacao_dados else None
                preco_vivo = cotacao_viva.preco if cotacao_viva else None
                atraso_candles = calcular_atraso_candles_minutos(pontos_originais)

                if periodo == "agora":
                    pontos = completar_serie_intraday_com_cotacao(pontos_originais, preco_vivo)
                else:
                    pontos = pontos_originais

                posicoes_x, valores, pontos_tooltip = self._montar_serie_intraday(pontos)
                if not valores:
                    self._label_status.configure(
                        text="Grafico intraday indisponivel (horarios invalidos).",
                        text_color=CORES["erro"],
                    )
                    return

                moeda = cotacao_dados[0].moeda if cotacao_dados[0] else "BRL"
                preco_fechamento_anterior = None
                if cotacao_viva is not None:
                    preco_fechamento_anterior = calcular_preco_fechamento_anterior(
                        cotacao_viva.preco,
                        cotacao_viva.variacao_valor,
                    )
                projecao = calcular_projecao_fim_dia(posicoes_x, valores)
                intervalo = "1 min" if periodo == "agora" else "5 min"
                titulo = f"Intraday — {codigo_exibicao(self._simbolo)} ({intervalo})"
                self._dados_grafico_atual = {
                    "posicoes_x": posicoes_x,
                    "valores": valores,
                    "titulo": titulo,
                    "simbolo": self._simbolo,
                    "moeda": moeda,
                    "pontos_tooltip": pontos_tooltip,
                    "preco_fechamento_anterior": preco_fechamento_anterior,
                    "projecao": projecao,
                }
                self._aplicar_dados_grafico(self._dados_grafico_atual)

                agora = datetime.now().strftime("%H:%M:%S")
                status = f"Ultima atualizacao as {agora} · intervalo {intervalo} · {len(pontos)} pontos"
                if projecao is not None:
                    status += (
                        f" · projecao fechamento {formatar_moeda(projecao.preco_fechamento_projetado, moeda)}"
                    )
                if periodo == "agora" and atraso_candles and atraso_candles >= 2:
                    status += (
                        f" · candles Yahoo ~{atraso_candles} min atrasados"
                        " · preco ao vivo ate o minuto atual"
                    )
                self._label_status.configure(
                    text=status,
                    text_color=CORES["textoSecundario"],
                )
            finally:
                self._bloqueio_foco_alerta = False
                self._pausar_mascaras_alerta(False)
                if editando_alerta:
                    self.after(
                        80,
                        lambda e=entrada_alerta_focada, c=cursor_alerta: self._restaurar_foco_entrada(
                            e,
                            c,
                        ),
                    )

        executar_em_thread(self, buscar, ao_concluir)

    def _deve_atualizar_metricas(self) -> bool:
        """Evita consultar metricas completas a cada 5 segundos."""
        if self._ultima_busca_metricas_ms <= 0:
            return True
        decorrido = int(time.monotonic() * 1000) - self._ultima_busca_metricas_ms
        return decorrido >= INTERVALO_METRICAS_MS

    def _aplicar_metricas_mercado(
        self,
        metricas: MetricasMercadoAgora,
        *,
        atualizar_variacao_5d: bool = True,
    ) -> None:
        self._ultima_busca_metricas_ms = int(time.monotonic() * 1000)
        self._preco_referencia_5_dias = metricas.preco_referencia_5_dias
        if self._painel_metricas is not None:
            self._painel_metricas.atualizar(metricas)
        if atualizar_variacao_5d:
            self._atualizar_variacao_5_dias(self._preco_atual_cotacao)
        if self._resumo_carteira is not None:
            self._atualizar_campos_carteira(self._preco_atual_cotacao)

    def _alternar_modelo_grafico(self, modelo: ModeloGrafico) -> None:
        self._modelo_grafico = modelo
        dados = self._dados_grafico_atual
        if not dados:
            return
        self._aplicar_dados_grafico(dados)

    def _grafico_tem_visualizacao_alterada(self) -> bool:
        """Indica zoom ou deslocamento manual em relacao a visao inicial."""
        if self._canvas is None or self._eixo is None or self._controle_zoom is None:
            return False

        controle = self._controle_zoom
        if controle._xlim_base is None or controle._ylim_base is None:
            return False

        if controle._esta_ampliado():
            return True

        tolerancia_x = 0.5
        span_y_base = max(controle._ylim_base[1] - controle._ylim_base[0], 1.0)
        tolerancia_y = span_y_base * 0.01

        xlim = self._eixo.get_xlim()
        ylim = self._eixo.get_ylim()
        for atual, base in zip(xlim, controle._xlim_base, strict=True):
            if abs(atual - base) > tolerancia_x:
                return True
        for atual, base in zip(ylim, controle._ylim_base, strict=True):
            if abs(atual - base) > tolerancia_y:
                return True
        return False

    def _aplicar_dados_grafico(self, dados: dict) -> None:
        if self._canvas is not None and self._eixo is not None:
            self._atualizar_serie_grafico_preservando_zoom(
                dados["posicoes_x"],
                dados["valores"],
                dados["titulo"],
                dados["simbolo"],
                dados["moeda"],
                dados["pontos_tooltip"],
            )
            return
        self._desenhar_grafico(
            dados["posicoes_x"],
            dados["valores"],
            dados["titulo"],
            dados["simbolo"],
            dados["moeda"],
            dados["pontos_tooltip"],
        )

    def _aplicar_camadas_grafico_agora(
        self,
        eixo,
        figura,
        posicoes_x: list[float],
        valores: list[float],
        pontos_tooltip: list[dict],
        *,
        titulo: str,
        moeda: str,
        preco_fechamento_anterior: float | None,
        projecao=None,
        xlim_fixo: tuple[float, float] | None = None,
        ylim_fixo: tuple[float, float] | None = None,
    ):
        posicoes = np.asarray(posicoes_x, dtype=float)
        if xlim_fixo is None or ylim_fixo is None:
            xlim, ylim = calcular_limites_eixo_agora(
                posicoes,
                valores,
                preco_fechamento_anterior=preco_fechamento_anterior,
                projecao=projecao,
            )
        else:
            xlim, ylim = xlim_fixo, ylim_fixo

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
        if projecao is not None:
            desenhar_projecao_fim_dia_agora(eixo, projecao, moeda, xlim)
        desenhar_linha_fechamento_anterior(eixo, preco_fechamento_anterior, moeda, xlim)
        configurar_eixo_intraday_agora(eixo, xlim, ylim)
        eixo.set_ylabel("")
        eixo.set_xlabel("")
        finalizar_figura_grafico(eixo, figura, titulo)
        if projecao is not None:
            legenda = eixo.legend(
                loc="upper left",
                fontsize=8,
                framealpha=0.85,
                facecolor=CORES.get("superficie", "#FFFFFF"),
                edgecolor=CORES.get("borda", "#E2E8F0"),
            )
            for texto in legenda.get_texts():
                texto.set_color(CORES.get("texto", "#0F172A"))
        return linha, xlim, ylim

    def _atualizar_serie_grafico_preservando_zoom(
        self,
        posicoes_x: list[float],
        valores: list[float],
        titulo: str,
        simbolo: str,
        moeda: str,
        pontos_tooltip: list[dict],
    ) -> None:
        """Atualiza apenas a serie, mantendo zoom e posicao do grafico."""
        if not valores or self._eixo is None or self._canvas is None or self._figura is None:
            self._desenhar_grafico(posicoes_x, valores, titulo, simbolo, moeda, pontos_tooltip)
            return

        xlim = self._eixo.get_xlim()
        ylim = self._eixo.get_ylim()
        preservar_zoom = self._grafico_tem_visualizacao_alterada()

        self._eixo.clear()

        dados = self._dados_grafico_atual or {}
        linha, _, _ = self._aplicar_camadas_grafico_agora(
            self._eixo,
            self._figura,
            posicoes_x,
            valores,
            pontos_tooltip,
            titulo=titulo,
            moeda=moeda,
            preco_fechamento_anterior=dados.get("preco_fechamento_anterior"),
            projecao=dados.get("projecao"),
            xlim_fixo=tuple(xlim) if preservar_zoom else None,
            ylim_fixo=tuple(ylim) if preservar_zoom else None,
        )

        if preservar_zoom:
            self._eixo.set_xlim(xlim)
            self._eixo.set_ylim(ylim)

        self._linha_grafico = linha
        configurar_tooltip_acao(
            self._canvas,
            self._eixo,
            linha,
            pontos_tooltip,
            simbolo,
            moeda,
            somente_horario=True,
        )
        self._canvas.draw_idle()

    def _montar_serie_intraday(self, pontos) -> tuple[list[float], list[float], list[dict]]:
        """Mapeia cada ponto para minutos do dia (eixo 10:00–18:00)."""
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
                    "volume": ponto.volume,
                    "minutos_dia": minutos,
                }
            )

        return posicoes_x, valores, pontos_tooltip

    def _atualizar_resumo_carteira(self) -> None:
        tinha_posicao = self._resumo_carteira is not None
        self._resumo_carteira = buscar_resumo_carteira(self._simbolo, self._linha_carteira)
        tem_posicao = self._resumo_carteira is not None
        if tinha_posicao != tem_posicao:
            self._sincronizar_painel_carteira_ou_compra()

    def _montar_alerta_topo_venda(self, pai: ctk.CTkFrame) -> None:
        fonte_titulo = ctk.CTkFont(size=14, weight="bold")
        fonte_destaque = ctk.CTkFont(size=16, weight="bold")
        fonte_resumo = ctk.CTkFont(size=13, weight="bold")

        ctk.CTkLabel(
            pai,
            text="Alerta venda — preco alvo (R$)",
            font=fonte_titulo,
            text_color=CORES["texto"],
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 6))

        linha_alerta = ctk.CTkFrame(pai, fg_color="transparent")
        linha_alerta.pack(fill="x", padx=12)

        self._entrada_alerta_valorizacao = ctk.CTkEntry(
            linha_alerta,
            width=170,
            height=38,
            font=fonte_destaque,
            placeholder_text="Ex.: R$ 70,00",
        )
        self._entrada_alerta_valorizacao.pack(side="left", padx=(0, 10))
        aplicar_mascara_moeda_ptbr(self._entrada_alerta_valorizacao)
        self._configurar_entrada_alerta(self._entrada_alerta_valorizacao)
        self._preencher_entrada_alerta()

        ctk.CTkButton(
            linha_alerta,
            text="Salvar alerta",
            command=self._salvar_alerta_valorizacao,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            font=ctk.CTkFont(size=13, weight="bold"),
            width=120,
            height=38,
        ).pack(side="left")

        self._label_variacao_5_dias_carteira = ctk.CTkLabel(
            pai,
            text="—",
            font=fonte_resumo,
            text_color=CORES["textoSecundario"],
            anchor="w",
            wraplength=480,
            justify="left",
        )
        self._label_variacao_5_dias_carteira.pack(anchor="w", padx=12, pady=(8, 10))

    def _montar_alerta_topo_compra(self, pai: ctk.CTkFrame) -> None:
        fonte_titulo = ctk.CTkFont(size=14, weight="bold")
        fonte_destaque = ctk.CTkFont(size=16, weight="bold")
        fonte_resumo = ctk.CTkFont(size=13, weight="bold")

        ctk.CTkLabel(
            pai,
            text="Alerta compra — preco alvo (R$)",
            font=fonte_titulo,
            text_color=CORES["texto"],
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 6))

        linha_alerta = ctk.CTkFrame(pai, fg_color="transparent")
        linha_alerta.pack(fill="x", padx=12)

        self._entrada_alerta_compra = ctk.CTkEntry(
            linha_alerta,
            width=170,
            height=38,
            font=fonte_destaque,
            placeholder_text="Ex.: R$ 43,50",
        )
        self._entrada_alerta_compra.pack(side="left", padx=(0, 10))
        aplicar_mascara_moeda_ptbr(self._entrada_alerta_compra)
        self._configurar_entrada_alerta(self._entrada_alerta_compra)
        self._preencher_entrada_alerta_compra()

        ctk.CTkButton(
            linha_alerta,
            text="Salvar alerta",
            command=self._salvar_alerta_compra,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            font=ctk.CTkFont(size=13, weight="bold"),
            width=120,
            height=38,
        ).pack(side="left")

        self._label_variacao_5_dias_compra = ctk.CTkLabel(
            pai,
            text="—",
            font=fonte_resumo,
            text_color=CORES["textoSecundario"],
            anchor="w",
            wraplength=480,
            justify="left",
        )
        self._label_variacao_5_dias_compra.pack(anchor="w", padx=12, pady=(8, 10))

    def _configurar_entrada_alerta(self, entrada: ctk.CTkEntry) -> None:
        entrada.bind("<FocusIn>", self._ao_focar_entrada_alerta, add="+")
        entrada.bind("<FocusOut>", self._ao_sair_foco_entrada_alerta, add="+")

    def _ao_focar_entrada_alerta(self, _evento=None) -> None:
        self._editando_alerta = True

    def _ao_sair_foco_entrada_alerta(self, _evento=None) -> None:
        if self._bloqueio_foco_alerta:
            return
        self.after(120, self._verificar_fim_edicao_alerta)

    def _verificar_fim_edicao_alerta(self) -> None:
        if not janela_ui_ainda_ativa(self):
            return
        if self._bloqueio_foco_alerta:
            self.after(120, self._verificar_fim_edicao_alerta)
            return
        if self._obter_entrada_alerta_com_foco() is None:
            self._editando_alerta = False
            self._atualizar_variacao_5_dias(self._preco_atual_cotacao)

    def _obter_entrada_alerta_com_foco(self) -> ctk.CTkEntry | None:
        foco = self.focus_get()
        if foco is None:
            return None
        for entrada in (self._entrada_alerta_valorizacao, self._entrada_alerta_compra):
            if foco == entrada:
                return entrada
            try:
                if foco == entrada._entry:
                    return entrada
            except AttributeError:
                pass
        return None

    def _salvar_estado_foco_alerta(self) -> tuple[ctk.CTkEntry | None, int | None]:
        entrada = self._obter_entrada_alerta_com_foco()
        if entrada is None:
            return None, None
        try:
            cursor = int(entrada._entry.index("insert"))
        except Exception:
            cursor = None
        return entrada, cursor

    def _entrada_alerta_em_edicao(self) -> bool:
        return self._obter_entrada_alerta_com_foco() is not None

    def _pausar_mascaras_alerta(self, pausar: bool) -> None:
        for entrada in (self._entrada_alerta_valorizacao, self._entrada_alerta_compra):
            entrada._mascara_pausada = pausar

    def _restaurar_foco_entrada(
        self,
        entrada: ctk.CTkEntry | None,
        cursor: int | None = None,
    ) -> None:
        alvo = entrada
        if alvo is None or not janela_ui_ainda_ativa(self):
            return
        try:
            if not alvo.winfo_exists():
                return
            widget_interno = getattr(alvo, "_entry", alvo)
            alvo.focus_set()
            widget_interno.focus_set()
            if cursor is not None:
                widget_interno.icursor(cursor)
            else:
                widget_interno.icursor("end")
        except Exception:
            pass

    def _sincronizar_painel_carteira_ou_compra(self) -> None:
        if self._resumo_carteira is not None:
            self._alerta_compra_ativo = False
            self._label_alerta_compra.pack_forget()
            self._frame_alerta_topo_compra.pack_forget()
            if not self._frame_alerta_topo_venda.winfo_ismapped():
                self._frame_alerta_topo_venda.pack(fill="both", expand=True)
            if not self._frame_painel_carteira.winfo_ismapped():
                self._frame_painel_carteira.pack(fill="x", pady=(0, 8))
            return

        self._frame_painel_carteira.pack_forget()
        self._alerta_venda_ativo = False
        self._label_alerta_venda.pack_forget()
        self._frame_alerta_topo_venda.pack_forget()
        if not self._frame_alerta_topo_compra.winfo_ismapped():
            self._frame_alerta_topo_compra.pack(fill="both", expand=True)

    def _preencher_entrada_alerta_compra(self) -> None:
        if self._alerta_compra_limite is None or self._alerta_compra_limite <= 0:
            return
        centavos = int(round(self._alerta_compra_limite * 100))
        self._entrada_alerta_compra.insert(0, f"R$ {formatar_centavos_ptbr(centavos)}")

    def _salvar_alerta_compra(self) -> None:
        texto = self._entrada_alerta_compra.get().strip()
        if not texto or texto == "R$":
            self._alerta_compra_limite = None
            try:
                self._config_painel.salvar_alerta_compra_acao(self._simbolo, None)
            except OSError:
                self._label_status.configure(
                    text="Nao foi possivel salvar o alerta no painel.ini.",
                    text_color=CORES["erro"],
                )
                return
            self._label_status.configure(
                text="Alerta de compra removido.",
                text_color=CORES["textoSecundario"],
            )
            self._verificar_alerta_compra(self._preco_atual_cotacao, None)
            return

        valor, erro = CarteiraServico.parse_preco(texto)
        if erro or valor is None or valor <= 0:
            self._label_status.configure(
                text=erro or "Informe um preco alvo valido em reais.",
                text_color=CORES["erro"],
            )
            return

        self._alerta_compra_limite = valor
        try:
            self._config_painel.salvar_alerta_compra_acao(self._simbolo, valor)
        except OSError:
            self._label_status.configure(
                text="Nao foi possivel salvar o alerta no painel.ini.",
                text_color=CORES["erro"],
            )
            return

        self._label_status.configure(
            text=f"Alerta salvo: comprar quando o preco atingir {formatar_moeda(valor)} ou menos.",
            text_color=CORES["sucesso"],
        )
        moeda = "BRL"
        if self._preco_atual_cotacao is not None:
            self._verificar_alerta_compra(self._preco_atual_cotacao, moeda)

    def _preencher_entrada_alerta(self) -> None:
        if self._alerta_preco_venda_limite is None or self._alerta_preco_venda_limite <= 0:
            return
        centavos = int(round(self._alerta_preco_venda_limite * 100))
        self._entrada_alerta_valorizacao.insert(0, f"R$ {formatar_centavos_ptbr(centavos)}")

    def _salvar_alerta_valorizacao(self) -> None:
        texto = self._entrada_alerta_valorizacao.get().strip()
        if not texto or texto == "R$":
            self._alerta_preco_venda_limite = None
            try:
                self._config_painel.salvar_alerta_preco_venda_agora(self._simbolo, None)
            except OSError:
                self._label_status.configure(
                    text="Nao foi possivel salvar o alerta no painel.ini.",
                    text_color=CORES["erro"],
                )
                return
            self._label_status.configure(
                text="Alerta de preco da acao removido.",
                text_color=CORES["textoSecundario"],
            )
            self._verificar_alerta_venda(self._preco_atual_cotacao)
            self._atualizar_resumo_alertas_lateral(self._preco_atual_cotacao)
            return

        valor, erro = CarteiraServico.parse_preco(texto)
        if erro or valor is None or valor <= 0:
            self._label_status.configure(
                text=erro or "Informe um preco alvo valido em reais.",
                text_color=CORES["erro"],
            )
            return

        self._alerta_preco_venda_limite = valor
        try:
            self._config_painel.salvar_alerta_preco_venda_agora(self._simbolo, valor)
        except OSError:
            self._label_status.configure(
                text="Nao foi possivel salvar o alerta no painel.ini.",
                text_color=CORES["erro"],
            )
            return

        moeda = self._resumo_carteira.moeda if self._resumo_carteira else "BRL"
        self._label_status.configure(
            text=(
                f"Alerta salvo: vender quando o preco da acao atingir "
                f"{formatar_moeda(valor, moeda)} ou mais."
            ),
            text_color=CORES["sucesso"],
        )
        self._verificar_alerta_venda(self._preco_atual_cotacao)
        self._atualizar_resumo_alertas_lateral(self._preco_atual_cotacao)

    def _atualizar_campos_carteira(self, preco_atual: float | None) -> None:
        if self._resumo_carteira is None:
            return

        resumo = self._resumo_carteira
        moeda = resumo.moeda
        self._label_carteira_qtd.configure(text=_formatar_quantidade(resumo.quantidade))
        self._label_carteira_compra.configure(text=formatar_moeda(resumo.preco_compra, moeda))

        if preco_atual is None or preco_atual <= 0:
            self._label_carteira_valorizacao.configure(text="—", text_color=CORES["textoSecundario"])
            self._verificar_alerta_venda(None)
            return

        valor_reais = resumo.valorizacao_reais(preco_atual)
        cor = CORES["sucesso"] if valor_reais >= 0 else CORES["erro"]
        self._label_carteira_valorizacao.configure(
            text=formatar_moeda(valor_reais, moeda),
            text_color=cor,
        )
        self._verificar_alerta_venda(preco_atual)

    def _atualizar_resumo_alertas_lateral(self, preco_atual: float | None) -> None:
        texto_carteira, cor_carteira = self._montar_resumo_alerta_lateral(
            preco_atual,
            incluir_compra=True,
        )
        texto_compra, cor_compra = self._montar_resumo_alerta_lateral(
            preco_atual,
            incluir_compra=False,
        )
        self._label_variacao_5_dias_carteira.configure(text=texto_carteira, text_color=cor_carteira)
        self._label_variacao_5_dias_compra.configure(text=texto_compra, text_color=cor_compra)

    def _montar_resumo_alerta_lateral(
        self,
        preco_atual: float | None,
        *,
        incluir_compra: bool,
    ) -> tuple[str, str]:
        if preco_atual is None or preco_atual <= 0:
            return "—", CORES["textoSecundario"]

        moeda = "BRL"
        if incluir_compra and self._resumo_carteira is not None:
            moeda = self._resumo_carteira.moeda
        elif not incluir_compra:
            moeda = "BRL" if self._simbolo.upper().endswith(".SA") else "USD"

        partes: list[str] = [formatar_moeda(preco_atual, moeda)]

        if incluir_compra and self._resumo_carteira is not None:
            pct_compra = self._resumo_carteira.valorizacao_percentual(preco_atual)
            if pct_compra is not None:
                sinal = "+" if pct_compra >= 0 else ""
                partes.append(f"{sinal}{pct_compra:.2f}% na compra")

        pct_5d = AgoraMetricasMercadoServico.calcular_variacao_percentual_5_dias(
            preco_atual,
            self._preco_referencia_5_dias,
        )
        if pct_5d is not None:
            icone = "▲" if pct_5d >= 0 else "▼"
            sinal = "+" if pct_5d >= 0 else ""
            partes.append(f"{icone} {sinal}{pct_5d:.2f}% em 5 dias")

        limite = self._alerta_preco_venda_limite if incluir_compra else None
        cor = CORES["textoSecundario"]
        if pct_5d is not None:
            cor = CORES["sucesso"] if pct_5d >= 0 else CORES["erro"]
        if incluir_compra and limite and preco_atual >= limite:
            cor = CORES["sucesso"]
            partes.append(f"preco alvo {formatar_moeda(limite, moeda)} atingido")

        return "  ·  ".join(partes), cor

    def _atualizar_variacao_5_dias(self, preco_atual: float | None) -> None:
        self._atualizar_resumo_alertas_lateral(preco_atual)

    def _formatar_carimbo_agora(self, moeda: str) -> str:
        """Data/hora no estilo da cotacao ao vivo (ex.: 17 de jun., 13:00:17 UTC-3 · BRL)."""
        agora = datetime.now()
        meses = (
            "jan.",
            "fev.",
            "mar.",
            "abr.",
            "mai.",
            "jun.",
            "jul.",
            "ago.",
            "set.",
            "out.",
            "nov.",
            "dez.",
        )
        codigo_moeda = "BRL" if moeda == "BRL" else "USD"
        return (
            f"{agora.day} de {meses[agora.month - 1]}, "
            f"{agora.strftime('%H:%M:%S')} UTC-3 · {codigo_moeda}"
        )

    def _atualizar_indicador_compra(self, preco_atual: float | None) -> None:
        """Exibe percentual e valor da posicao em relacao ao preco de compra."""
        if self._resumo_carteira is None or preco_atual is None or preco_atual <= 0:
            self._label_variacao_compra.pack_forget()
            return

        resumo = self._resumo_carteira
        valor_reais = resumo.valorizacao_reais(preco_atual)
        valor_pct = resumo.valorizacao_percentual(preco_atual)
        if valor_pct is None:
            self._label_variacao_compra.pack_forget()
            return

        cor = CORES["sucesso"] if valor_reais >= 0 else CORES["erro"]
        self._label_variacao_compra.configure(
            text=formatar_variacao_com_rotulo(
                valor_reais,
                valor_pct,
                "Na sua compra",
                resumo.moeda,
            ),
            text_color=cor,
        )
        if not self._label_variacao_compra.winfo_ismapped():
            self._label_variacao_compra.pack(anchor="w", pady=(4, 0))

    def _verificar_alerta_venda(self, preco_atual: float | None) -> None:
        limite = self._alerta_preco_venda_limite
        if (
            limite is None
            or limite <= 0
            or preco_atual is None
            or preco_atual < limite
        ):
            self._alerta_venda_ativo = False
            self._label_alerta_venda.pack_forget()
            return

        self._alerta_venda_ativo = True
        moeda = self._resumo_carteira.moeda if self._resumo_carteira else "BRL"
        self._label_alerta_venda.configure(
            text=(
                f"VENDER — o preco da acao atingiu {formatar_moeda(preco_atual, moeda)} "
                f"(alerta: {formatar_moeda(limite, moeda)} ou mais). "
                "Considere realizar a venda."
            ),
            fg_color=CORES["erro"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        )
        if not self._label_alerta_venda.winfo_ismapped():
            self._label_alerta_venda.pack(fill="x", padx=16, pady=(8, 10))

    def _verificar_alerta_compra(self, preco_atual: float | None, moeda: str | None) -> None:
        if self._resumo_carteira is not None:
            self._alerta_compra_ativo = False
            self._label_alerta_compra.pack_forget()
            return

        limite = self._alerta_compra_limite
        if limite is None or limite <= 0 or preco_atual is None or preco_atual <= 0:
            self._alerta_compra_ativo = False
            self._label_alerta_compra.pack_forget()
            return

        moeda_fmt = moeda or "BRL"
        if preco_atual <= limite:
            self._alerta_compra_ativo = True
            self._label_alerta_compra.configure(
                text=(
                    f"COMPRAR — o preco atual {formatar_moeda(preco_atual, moeda_fmt)} "
                    f"esta no alvo ou abaixo de {formatar_moeda(limite, moeda_fmt)}. "
                    "Considere realizar a compra."
                ),
                fg_color=CORES["sucesso"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
            )
            if not self._label_alerta_compra.winfo_ismapped():
                self._label_alerta_compra.pack(fill="x", padx=16, pady=(8, 10))
            return

        self._alerta_compra_ativo = False
        self._label_alerta_compra.pack_forget()

    def _atualizar_painel_preco(
        self,
        cotacao_dados: tuple,
        *,
        atualizar_variacao_5d: bool = True,
    ) -> None:
        cotacao, taxa, aviso = cotacao_dados
        if cotacao is None:
            self._preco_atual_cotacao = None
            self._label_preco.configure(text="—")
            self._label_variacao_dia.configure(
                text=aviso or "Cotacao indisponivel",
                text_color=CORES["erro"],
            )
            self._label_variacao_compra.pack_forget()
            self._label_detalhes.configure(text="")
            self._atualizar_campos_carteira(None)
            if atualizar_variacao_5d:
                self._atualizar_variacao_5_dias(None)
            self._verificar_alerta_compra(None, None)
            return

        moeda = cotacao.moeda or "BRL"
        self._preco_atual_cotacao = cotacao.preco
        self._label_preco.configure(text=formatar_moeda(cotacao.preco, moeda))

        cor_var = CORES["sucesso"] if cotacao.variacao_percentual >= 0 else CORES["erro"]
        self._label_variacao_dia.configure(
            text=formatar_variacao_com_rotulo(
                cotacao.variacao_valor,
                cotacao.variacao_percentual,
                "Hoje",
                moeda,
            ),
            text_color=cor_var,
        )

        nome = cotacao.nome or codigo_exibicao(cotacao.simbolo)
        detalhes = [nome, self._formatar_carimbo_agora(moeda)]
        if taxa:
            detalhes.append(f"US$ 1 = {formatar_moeda(taxa, 'BRL')}")
        if aviso:
            detalhes.append(aviso)
        self._label_detalhes.configure(text="  ·  ".join(detalhes))
        self._atualizar_indicador_compra(cotacao.preco)
        self._atualizar_campos_carteira(cotacao.preco)
        if atualizar_variacao_5d:
            self._atualizar_variacao_5_dias(cotacao.preco)
        self._verificar_alerta_compra(cotacao.preco, moeda)

    def _desenhar_grafico(
        self,
        posicoes_x: list[float],
        valores: list[float],
        titulo: str,
        simbolo: str,
        moeda: str,
        pontos_tooltip: list[dict],
        tentativa: int = 0,
    ) -> None:
        if not valores:
            return

        if not self._area_grafico_pronta():
            if tentativa < 40:
                self.after(
                    80,
                    lambda: self._desenhar_grafico(
                        posicoes_x,
                        valores,
                        titulo,
                        simbolo,
                        moeda,
                        pontos_tooltip,
                        tentativa + 1,
                    ),
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
        self._eixo = None
        self._linha_grafico = None
        self._controle_zoom = None

        largura_px = max(400, self._medir_largura_frame_grafico())
        altura_px = max(120, self._medir_altura_frame_grafico())
        dpi = 100
        figura = Figure(
            figsize=(largura_px / dpi, altura_px / dpi),
            dpi=dpi,
            facecolor=CORES.get("graficoFundo", CORES["superficie"]),
        )
        eixo = figura.add_subplot(111)
        dados = self._dados_grafico_atual or {}
        linha, _, _ = self._aplicar_camadas_grafico_agora(
            eixo,
            figura,
            posicoes_x,
            valores,
            pontos_tooltip,
            titulo=titulo,
            moeda=moeda,
            preco_fechamento_anterior=dados.get("preco_fechamento_anterior"),
            projecao=dados.get("projecao"),
        )

        canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)
        configurar_tooltip_acao(
            canvas,
            eixo,
            linha,
            pontos_tooltip,
            simbolo,
            moeda,
            somente_horario=True,
        )
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        self._figura = figura
        self._canvas = canvas
        self._eixo = eixo
        self._linha_grafico = linha
        self._controle_zoom = criar_controle_zoom(canvas, eixo)
        self.after(80, lambda: self._ajustar_grafico_ao_redimensionar(0))

    def _medir_largura_frame_grafico(self) -> int:
        self._frame_grafico.update_idletasks()
        return max(1, self._frame_grafico.winfo_width() - 16)

    def _medir_altura_frame_grafico(self) -> int:
        self._frame_grafico.update_idletasks()
        return max(1, self._frame_grafico.winfo_height() - 16)

    def _area_grafico_pronta(self) -> bool:
        try:
            return (
                self._frame_grafico.winfo_width() > 120
                and self._frame_grafico.winfo_height() > 120
            )
        except Exception:
            return False

    def _ao_configurar_frame_grafico(self, event) -> None:
        if event.widget is not self._frame_grafico:
            return
        if self._job_redimensionar_grafico is not None:
            try:
                self.after_cancel(self._job_redimensionar_grafico)
            except Exception:
                pass
        self._job_redimensionar_grafico = self.after(
            120,
            self._executar_redimensionamento_grafico,
        )

    def _executar_redimensionamento_grafico(self) -> None:
        self._job_redimensionar_grafico = None
        self._ajustar_grafico_ao_redimensionar()

    def _ao_layout_inicial(self) -> None:
        ajustar_janela_area_trabalho(self)
        self._ajustar_grafico_ao_redimensionar()

    def _ajustar_grafico_ao_redimensionar(self, tentativa: int = 0) -> None:
        if self._canvas is None or self._figura is None:
            if tentativa < 30:
                self.after(100, lambda: self._ajustar_grafico_ao_redimensionar(tentativa + 1))
            return
        try:
            if not self._area_grafico_pronta():
                if tentativa < 30:
                    self.after(100, lambda: self._ajustar_grafico_ao_redimensionar(tentativa + 1))
                return
            largura_px = max(400, self._medir_largura_frame_grafico())
            altura_px = max(120, self._medir_altura_frame_grafico())
            dpi = self._figura.get_dpi()
            self._figura.set_size_inches(largura_px / dpi, altura_px / dpi, forward=True)
            self._canvas.draw_idle()
        except Exception:
            pass


def abrir_grafico_tempo_real(
    pai: ctk.CTk,
    controlador: Any,
    simbolo: str,
    linha_carteira: LinhaCarteira | None = None,
) -> JanelaGraficoTempoReal | None:
    """Abre a tela Agora para acompanhar o ativo em tempo quase real."""
    if not pai.winfo_exists():
        return None
    return JanelaGraficoTempoReal(pai, controlador, simbolo, linha_carteira=linha_carteira)
