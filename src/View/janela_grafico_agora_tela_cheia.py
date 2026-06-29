"""Grafico intraday da tela Agora em janela maximizada, sincronizado com a tela principal."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.Model.opcoes_medias_moveis_grafico import OpcoesMediasMoveisGrafico
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import configurar_janela_maximizada, janela_ui_ainda_ativa
from src.View.grafico_agora_helper import (
    calcular_limites_eixo_agora,
    configurar_eixo_intraday_agora,
    criar_subplots_agora,
    desenhar_linha_fechamento_anterior,
    desenhar_projecao_fim_dia_agora,
    desenhar_serie_agora,
    desenhar_volume_agora,
    finalizar_figura_grafico_agora,
    obter_cor_tendencia_agora,
    ocultar_rotulos_eixo_x_preco,
)
from src.View.grafico_helper import configurar_tooltip_acao
from src.View.grafico_marcador_cruz_helper import reaplicar_marcador_cruz_canvas
from src.View.grafico_medias_moveis_helper import (
    aplicar_legenda_com_medias,
    desenhar_medias_moveis,
    montar_botao_config_medias_moveis_grafico,
    valores_medias_para_limites,
)
from src.View.grafico_modelo_helper import ModeloGrafico, montar_seletor_modelo_grafico, rotulo_por_chave_modelo
from src.View.grafico_zoom_helper import criar_controle_zoom, montar_botoes_zoom_grafico
from src.View.tema import CORES

_ALTURA_DESENHO_MIN_PX = 320


class JanelaGraficoAgoraTelaCheia(ctk.CTkToplevel):
    """Exibe o intraday em tela cheia e acompanha as atualizacoes da tela Agora."""

    def __init__(
        self,
        pai_agora: ctk.CTkToplevel,
        *,
        titulo_janela: str,
        dados_iniciais: dict | None,
        obter_modelo: Callable[[], ModeloGrafico],
        obter_opcoes_medias: Callable[[], OpcoesMediasMoveisGrafico],
        config_painel: ConfigPainelIni,
        ao_mudar_modelo: Callable[[ModeloGrafico], None],
        ao_alterar_medias: Callable[[], None],
        ao_fechar: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(pai_agora)
        self._pai_agora = pai_agora
        self._obter_modelo = obter_modelo
        self._obter_opcoes_medias = obter_opcoes_medias
        self._config_painel = config_painel
        self._ao_mudar_modelo = ao_mudar_modelo
        self._ao_alterar_medias = ao_alterar_medias
        self._ao_fechar_externo = ao_fechar
        self._modelo_grafico = obter_modelo()
        self._combo_modelo: ctk.CTkComboBox | None = None
        self._controles_medias_moveis = None
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._eixo = None
        self._eixo_volume = None
        self._controle_zoom = None
        self._job_redimensionar: str | None = None

        self.title(titulo_janela)
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 620)

        self._montar_interface()
        configurar_janela_maximizada(
            self,
            ao_apos_layout=self._ajustar_grafico_ao_redimensionar,
            janela_pai=pai_agora,
        )
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

        if dados_iniciais:
            self.atualizar_grafico(
                dados_iniciais,
                self._modelo_grafico,
                obter_opcoes_medias(),
            )
        self.after(120, self._ajustar_grafico_ao_redimensionar)

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Grafico em tela cheia",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Acompanha o grafico da tela Agora enquanto esta janela estiver aberta. "
                "Use Zoom -/+ ou a roda do mouse e arraste para mover apos ampliar."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=960,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 10))

        barra_zoom = ctk.CTkFrame(self, fg_color="transparent")
        barra_zoom.pack(fill="x", padx=16, pady=(0, 4))
        montar_botoes_zoom_grafico(barra_zoom, lambda: self._controle_zoom)
        self._controles_medias_moveis = montar_botao_config_medias_moveis_grafico(
            barra_zoom,
            self._config_painel,
            self._ao_alterar_medias,
        )

        barra_modelo = ctk.CTkFrame(barra_zoom, fg_color="transparent")
        barra_modelo.pack(side="right", padx=(8, 0))
        self._combo_modelo = montar_seletor_modelo_grafico(
            barra_modelo,
            modelo_inicial=self._modelo_grafico,
            ao_mudar=self._alternar_modelo_grafico,
            largura_combo=110,
        )

        self._frame_grafico = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._frame_grafico.pack(fill="both", expand=True, padx=16, pady=(8, 8))
        self._frame_grafico.bind("<Configure>", self._ao_configurar_frame_grafico)

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

    def _alternar_modelo_grafico(self, modelo: ModeloGrafico) -> None:
        self._modelo_grafico = modelo
        self._ao_mudar_modelo(modelo)

    def _sincronizar_combo_modelo(self, modelo: ModeloGrafico) -> None:
        if self._combo_modelo is None:
            return
        rotulo = rotulo_por_chave_modelo(modelo)
        if self._combo_modelo.get() != rotulo:
            self._combo_modelo.set(rotulo)

    def atualizar_grafico(
        self,
        dados: dict,
        modelo: ModeloGrafico | None = None,
        opcoes_medias: OpcoesMediasMoveisGrafico | None = None,
    ) -> None:
        if not janela_ui_ainda_ativa(self):
            return

        self._modelo_grafico = modelo or self._obter_modelo()
        self._sincronizar_combo_modelo(self._modelo_grafico)
        opcoes = opcoes_medias or self._obter_opcoes_medias()
        posicoes_x = dados.get("posicoes_x") or []
        valores = dados.get("valores") or []
        if not valores:
            return

        if self._canvas is not None and self._eixo is not None:
            self._atualizar_serie_preservando_zoom(
                dados,
                posicoes_x,
                valores,
                opcoes,
            )
            return

        self._desenhar_grafico(dados, posicoes_x, valores, opcoes)

    def _desenhar_grafico(
        self,
        dados: dict,
        posicoes_x: list[float],
        valores: list[float],
        opcoes_medias: OpcoesMediasMoveisGrafico,
        tentativa: int = 0,
    ) -> None:
        if not self._area_grafico_pronta():
            if tentativa < 40:
                self.after(
                    80,
                    lambda: self._desenhar_grafico(
                        dados,
                        posicoes_x,
                        valores,
                        opcoes_medias,
                        tentativa + 1,
                    ),
                )
            return

        self._limpar_grafico()

        largura_px = max(600, self._medir_largura_frame_grafico())
        altura_px = max(_ALTURA_DESENHO_MIN_PX, self._medir_altura_frame_grafico())
        dpi = 100
        figura = Figure(
            figsize=(largura_px / dpi, altura_px / dpi),
            dpi=dpi,
            facecolor=CORES.get("graficoFundo", CORES["superficie"]),
        )
        eixo, eixo_volume = criar_subplots_agora(figura)
        linha, _, _ = self._aplicar_camadas(
            eixo,
            figura,
            eixo_volume,
            dados,
            posicoes_x,
            valores,
            opcoes_medias,
        )

        canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)
        self._configurar_tooltip(
            canvas,
            eixo,
            linha,
            dados.get("pontos_tooltip") or [],
            dados.get("simbolo", ""),
            dados.get("moeda", "BRL"),
        )
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        self._figura = figura
        self._canvas = canvas
        self._eixo = eixo
        self._eixo_volume = eixo_volume
        self._controle_zoom = criar_controle_zoom(canvas, eixo, eixo_volume=eixo_volume)
        self.after(80, lambda: self._ajustar_grafico_ao_redimensionar(0))

    def _atualizar_serie_preservando_zoom(
        self,
        dados: dict,
        posicoes_x: list[float],
        valores: list[float],
        opcoes_medias: OpcoesMediasMoveisGrafico,
    ) -> None:
        if self._eixo is None or self._canvas is None or self._figura is None:
            self._desenhar_grafico(dados, posicoes_x, valores, opcoes_medias)
            return

        xlim = self._eixo.get_xlim()
        ylim = self._eixo.get_ylim()
        preservar_zoom = self._grafico_tem_visualizacao_alterada()

        self._eixo.clear()
        if self._eixo_volume is not None:
            self._eixo_volume.clear()

        linha, _, _ = self._aplicar_camadas(
            self._eixo,
            self._figura,
            self._eixo_volume,
            dados,
            posicoes_x,
            valores,
            opcoes_medias,
            xlim_fixo=tuple(xlim) if preservar_zoom else None,
            ylim_fixo=tuple(ylim) if preservar_zoom else None,
        )

        if preservar_zoom:
            self._eixo.set_xlim(xlim)
            self._eixo.set_ylim(ylim)

        self._configurar_tooltip(
            self._canvas,
            self._eixo,
            linha,
            dados.get("pontos_tooltip") or [],
            dados.get("simbolo", ""),
            dados.get("moeda", "BRL"),
        )
        reaplicar_marcador_cruz_canvas(
            self._canvas,
            self._eixo,
            eixo_volume=self._eixo_volume,
        )
        self._canvas.draw_idle()

    def _aplicar_camadas(
        self,
        eixo,
        figura,
        eixo_volume,
        dados: dict,
        posicoes_x: list[float],
        valores: list[float],
        opcoes_medias: OpcoesMediasMoveisGrafico,
        *,
        xlim_fixo: tuple[float, float] | None = None,
        ylim_fixo: tuple[float, float] | None = None,
    ):
        posicoes = np.asarray(posicoes_x, dtype=float)
        preco_fechamento_anterior = dados.get("preco_fechamento_anterior")
        projecao = dados.get("projecao")
        moeda = dados.get("moeda", "BRL")
        titulo = dados.get("titulo", "Intraday")

        extras_y = valores_medias_para_limites(valores, opcoes_medias)
        if xlim_fixo is None or ylim_fixo is None:
            xlim, ylim = calcular_limites_eixo_agora(
                posicoes,
                valores,
                preco_fechamento_anterior=preco_fechamento_anterior,
                projecao=projecao,
                referencias_y_extra=extras_y,
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
            dados.get("pontos_tooltip") or [],
            modelo=self._modelo_grafico,
            cor=cor,
            y_base=ylim[0],
        )
        if projecao is not None:
            desenhar_projecao_fim_dia_agora(eixo, projecao, moeda, xlim)
        desenhar_linha_fechamento_anterior(eixo, preco_fechamento_anterior, moeda, xlim)
        tem_medias = desenhar_medias_moveis(eixo, posicoes, valores, opcoes_medias)
        configurar_eixo_intraday_agora(eixo, xlim, ylim)
        eixo.set_ylabel("")
        eixo.set_xlabel("")
        com_volume = eixo_volume is not None
        if com_volume:
            ocultar_rotulos_eixo_x_preco(eixo)
            desenhar_volume_agora(
                eixo_volume,
                figura,
                posicoes,
                dados.get("pontos_tooltip") or [],
                xlim,
            )
        finalizar_figura_grafico_agora(eixo, figura, titulo, com_painel_volume=com_volume)
        if projecao is not None or tem_medias:
            aplicar_legenda_com_medias(eixo)
        return linha, xlim, ylim

    def _configurar_tooltip(
        self,
        canvas: FigureCanvasTkAgg,
        eixo,
        linha,
        pontos_tooltip: list[dict],
        simbolo: str,
        moeda: str,
    ) -> None:
        configurar_tooltip_acao(
            canvas,
            eixo,
            linha,
            pontos_tooltip,
            simbolo,
            moeda,
            somente_horario=True,
            eixo_volume=self._eixo_volume,
        )

    def _grafico_tem_visualizacao_alterada(self) -> bool:
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

    def _limpar_grafico(self) -> None:
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
        self._eixo_volume = None
        self._controle_zoom = None

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
        if self._job_redimensionar is not None:
            try:
                self.after_cancel(self._job_redimensionar)
            except Exception:
                pass
        self._job_redimensionar = self.after(120, self._executar_redimensionamento_grafico)

    def _executar_redimensionamento_grafico(self) -> None:
        self._job_redimensionar = None
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
            largura_px = max(600, self._medir_largura_frame_grafico())
            altura_px = max(_ALTURA_DESENHO_MIN_PX, self._medir_altura_frame_grafico())
            dpi = self._figura.get_dpi()
            self._figura.set_size_inches(largura_px / dpi, altura_px / dpi, forward=True)
            self._canvas.draw_idle()
        except Exception:
            pass

    def _ao_fechar(self) -> None:
        if self._job_redimensionar is not None:
            try:
                self.after_cancel(self._job_redimensionar)
            except Exception:
                pass
            self._job_redimensionar = None
        self._limpar_grafico()
        if self._ao_fechar_externo is not None:
            self._ao_fechar_externo()
        self.destroy()


def atualizar_estado_botao_grafico_tela_cheia(botao: ctk.CTkButton, grafico_pronto: bool) -> None:
    """Habilita o botao quando o grafico ja foi carregado na tela Agora."""
    botao.configure(state="normal" if grafico_pronto else "disabled")


def abrir_grafico_agora_tela_cheia(
    pai_agora: ctk.CTkToplevel,
    *,
    titulo_janela: str,
    dados_iniciais: dict | None,
    obter_modelo: Callable[[], ModeloGrafico],
    obter_opcoes_medias: Callable[[], OpcoesMediasMoveisGrafico],
    config_painel: ConfigPainelIni,
    ao_mudar_modelo: Callable[[ModeloGrafico], None],
    ao_alterar_medias: Callable[[], None],
    ao_fechar: Callable[[], None] | None = None,
) -> JanelaGraficoAgoraTelaCheia | None:
    if not pai_agora.winfo_exists() or not dados_iniciais:
        return None
    return JanelaGraficoAgoraTelaCheia(
        pai_agora,
        titulo_janela=titulo_janela,
        dados_iniciais=dados_iniciais,
        obter_modelo=obter_modelo,
        obter_opcoes_medias=obter_opcoes_medias,
        config_painel=config_painel,
        ao_mudar_modelo=ao_mudar_modelo,
        ao_alterar_medias=ao_alterar_medias,
        ao_fechar=ao_fechar,
    )
