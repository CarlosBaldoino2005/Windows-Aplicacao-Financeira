"""Janela dedicada para grafico de historico de uma acao."""
from __future__ import annotations


import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from typing import Any

from src.Controller.controlador_mercado import ControladorMercado
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.Tool.mascara_moeda_helper import aplicar_mascara_inteiro_ptbr, formatar_inteiro_ptbr
from src.Tool.validadores import validar_quantidade_cotas
from src.Service.cdi_servico import CdiServico
from src.View.grafico_modelo_helper import (
    ModeloGrafico,
    desenhar_serie_preco_principal,
    montar_seletor_modelo_grafico,
)
from src.View.grafico_helper import (
    COR_LINHA_CDI,
    TEXTO_INSTRUCAO_GRAFICO_ACAO,
    aplicar_tema_matplotlib,
    configurar_rotulos_eixo_x,
    configurar_selecao_periodo,
    configurar_tooltip_acao,
)
from src.Tool.cotacao_dual_helper import codigo_exibicao, rotulo_tipo_ativo
from src.View.destaque_cotacao_helper import PainelDestaqueCotacao, iniciar_atualizacao_destaque
from src.View.janela_calcular_quantidade import JanelaCalcularQuantidade
from src.View.janela_desvalorizacao import JanelaDesvalorizacao
from src.View.janela_adicionar_monitoramento import abrir_adicionar_monitoramento
from src.Controller.controlador_monitoramento import ControladorMonitoramento
from src.Tool.controlador_ativo_helper import inferir_tipo_ativo_monitoramento
from src.Model.periodos_mercado import PERIODOS_MERCADO, rotulo_periodo_por_chave
from src.View.grafico_helper import _publicar_payload_com_cdi
from src.View.grafico_zoom_helper import criar_controle_zoom, montar_botoes_zoom_grafico
from src.View.janela_grafico_ampliado import (
    abrir_grafico_ampliado_acao,
    atualizar_estado_botao_grafico_ampliado,
)
from src.View.janela_resumo_periodo import (
    abrir_janela_resumo_periodo,
    atualizar_estado_botao_resumo_ampliado,
)
from src.View.painel_comparacao_periodo import (
    PainelComparacaoPeriodo,
    calcular_comparacao_acao_unica,
    payload_instrucao,
)
from src.View.tema import CORES
from src.View import mensagem_helper as messagebox
from src.View.janela_blacklist_ativos import abrir_blacklist_ativos
from src.View.janela_grafico_tempo_real import abrir_grafico_tempo_real

PERIODOS = PERIODOS_MERCADO
ALTURA_GRAFICO_PX = 480


class JanelaGraficoAcao(ctk.CTkToplevel):
    """Tela ampla com periodo, grafico, tooltip e selecao de intervalo."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: ControladorMercado | Any,
        simbolo: str,
        periodo_chave: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._simbolo = simbolo
        self._periodo_inicial = periodo_chave
        self._data_inicio_inicial = (data_inicio or "").strip()
        self._data_fim_inicial = (data_fim or "").strip()
        self._figura: Figure | None = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._janela_detalhes: ctk.CTkToplevel | None = None
        self._janela_desvalorizacao: JanelaDesvalorizacao | None = None
        self._janela_calcular_quantidade: JanelaCalcularQuantidade | None = None
        self._janela_resumo_periodo: ctk.CTkToplevel | None = None
        self._janela_grafico_ampliado: ctk.CTkToplevel | None = None
        self._janela_adicionar_monitoramento: ctk.CTkToplevel | None = None
        self._janela_grafico_agora: ctk.CTkToplevel | None = None
        self._janela_blacklist: ctk.CTkToplevel | None = None
        self._controlador_monitoramento = ControladorMonitoramento()
        self._config_ini = ConfigPainelIni()
        self._payload_resumo_periodo: dict = payload_instrucao(TEXTO_INSTRUCAO_GRAFICO_ACAO)
        self._dados_grafico_atual: dict | None = None
        self._controle_zoom = None
        self._carregando_grafico = False
        self._modelo_grafico: ModeloGrafico = "linha"

        codigo = codigo_exibicao(simbolo)
        self.title(f"Grafico — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 600)

        self._montar_interface()
        self._aplicar_periodo_inicial()
        configurar_janela_maximizada(
            self,
            ao_apos_layout=self._ajustar_grafico_ao_redimensionar,
            janela_pai=pai,
        )
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self._atualizar_destaque_cotacao()
        # Aguarda a maximizacao na abertura antes de desenhar o grafico.
        self.after(950, self._carregar_grafico)

    def _ao_fechar(self) -> None:
        self._persistir_quantidade_cotas_ini()
        for attr in (
            "_janela_detalhes",
            "_janela_desvalorizacao",
            "_janela_calcular_quantidade",
            "_janela_resumo_periodo",
            "_janela_grafico_ampliado",
            "_janela_adicionar_monitoramento",
            "_janela_grafico_agora",
            "_janela_blacklist",
        ):
            janela = getattr(self, attr, None)
            if janela is not None:
                try:
                    if janela.winfo_exists():
                        janela.destroy()
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
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(side="top", fill="x")

        codigo = codigo_exibicao(self._simbolo)
        tipo = rotulo_tipo_ativo(self._simbolo)
        ctk.CTkLabel(
            cabecalho,
            text=f"Grafico — {codigo} ({tipo})",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self._painel_destaque_cotacao = PainelDestaqueCotacao(cabecalho)
        self._painel_destaque_cotacao.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Ao carregar, o resumo do periodo escolhido aparece abaixo (preco, lucro, dividendos e CDI). "
                "Use Zoom -/+ ou a roda do mouse. Apos ampliar, arraste o grafico com o mouse para mover. "
                "Passe o mouse para detalhes e clique em 2 pontos para comparar outro intervalo."
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

        self._combo_modelo_grafico = montar_seletor_modelo_grafico(
            barra,
            modelo_inicial=self._modelo_grafico,
            ao_mudar=self._alternar_modelo_grafico,
        )

        ctk.CTkButton(
            barra,
            text="Atualizar grafico",
            command=self._carregar_grafico,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            barra,
            text="Agora",
            command=self._abrir_grafico_agora,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=90,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            barra,
            text="Black List",
            command=self._abrir_blacklist,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=110,
        ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(barra, text="Qtd. de acoes").pack(side="left", padx=(0, 6))
        self._entrada_quantidade_cotas = ctk.CTkEntry(barra, width=110, justify="center")
        qtd_ini = self._config_ini.carregar_quantidade_cotas_grafico()
        self._entrada_quantidade_cotas.insert(0, formatar_inteiro_ptbr(qtd_ini))
        aplicar_mascara_inteiro_ptbr(self._entrada_quantidade_cotas)
        self._entrada_quantidade_cotas.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            barra,
            text="Calcular",
            command=self._abrir_calcular_quantidade,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=90,
        ).pack(side="left", padx=(0, 16))

        ctk.CTkButton(
            barra,
            text="Desvalorizacao",
            command=self._abrir_desvalorizacao,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=130,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            barra,
            text="Mais detalhes",
            command=self._abrir_mais_detalhes,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=130,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            barra,
            text="Monitoramento",
            command=self._abrir_monitoramento,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
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
        self._label_status.pack(anchor="w", padx=16, pady=(0, 8))

        self._area_rolagem = ctk.CTkScrollableFrame(
            self,
            fg_color=CORES["fundo"],
            label_text="Resumo e grafico — role para ver o grafico completo",
        )
        self._area_rolagem.pack(fill="both", expand=True, padx=0, pady=0)

        barra_resumo = ctk.CTkFrame(self._area_rolagem, fg_color="transparent")
        barra_resumo.pack(fill="x", padx=16, pady=(8, 4))
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

        self._frame_painel_periodo = ctk.CTkScrollableFrame(
            self._area_rolagem,
            height=240,
            fg_color=CORES["fundo"],
            label_text="Resumo do periodo selecionado no grafico",
        )
        self._frame_painel_periodo.pack(fill="x", padx=16, pady=(0, 8))
        self._exibir_resumo_periodo(self._payload_resumo_periodo)

        barra_grafico = ctk.CTkFrame(self._area_rolagem, fg_color="transparent")
        barra_grafico.pack(fill="x", padx=16, pady=(4, 0))
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

        self._frame_grafico = ctk.CTkFrame(
            self._area_rolagem,
            fg_color=CORES["superficie"],
            corner_radius=12,
            height=ALTURA_GRAFICO_PX,
        )
        self._frame_grafico.pack(fill="x", padx=16, pady=(8, 16))
        self._frame_grafico.pack_propagate(False)

    def _aplicar_periodo_inicial(self) -> None:
        if self._periodo_inicial:
            self._combo_periodo.set(rotulo_periodo_por_chave(self._periodo_inicial))
            self._alternar_datas()
        if self._data_inicio_inicial:
            self._entrada_inicio.delete(0, "end")
            self._entrada_inicio.insert(0, self._data_inicio_inicial)
        if self._data_fim_inicial:
            self._entrada_fim.delete(0, "end")
            self._entrada_fim.insert(0, self._data_fim_inicial)
        rotulo = self._combo_periodo.get()
        self._frame_painel_periodo.configure(label_text=f"Resumo do periodo: {rotulo}")

    def _periodo_chave(self) -> str:
        rotulo = self._combo_periodo.get()
        for chave, nome in PERIODOS:
            if nome == rotulo:
                return chave
        return "mes"

    def _atualizar_rotulo_painel_periodo(self) -> None:
        self._frame_painel_periodo.configure(
            label_text=f"Resumo do periodo: {self._combo_periodo.get()}"
        )

    def _exibir_resumo_periodo(self, payload: dict) -> None:
        self._payload_resumo_periodo = payload
        PainelComparacaoPeriodo.exibir(self._frame_painel_periodo, payload)
        atualizar_estado_botao_resumo_ampliado(self._btn_resumo_ampliado, payload)

    def _abrir_grafico_ampliado(self) -> None:
        if self._janela_grafico_ampliado is not None:
            try:
                if self._janela_grafico_ampliado.winfo_exists():
                    self._janela_grafico_ampliado.focus_force()
                    return
            except Exception:
                pass
        titulo = f"Grafico ampliado — {codigo_exibicao(self._simbolo)} — {self._combo_periodo.get()}"
        self._janela_grafico_ampliado = abrir_grafico_ampliado_acao(
            self,
            titulo,
            self._dados_grafico_atual,
            self._obter_quantidade_cotas_para_grafico,
            self._exibir_resumo_periodo,
        )

    def _abrir_resumo_periodo_ampliado(self) -> None:
        if self._janela_resumo_periodo is not None:
            try:
                if self._janela_resumo_periodo.winfo_exists():
                    self._janela_resumo_periodo.focus_force()
                    return
            except Exception:
                pass
        titulo = f"Resumo do periodo — {self._combo_periodo.get()} — {codigo_exibicao(self._simbolo)}"
        self._janela_resumo_periodo = abrir_janela_resumo_periodo(
            self, self._payload_resumo_periodo, titulo
        )

    def _abrir_calcular_quantidade(self) -> None:
        if self._janela_calcular_quantidade is not None:
            try:
                if self._janela_calcular_quantidade.winfo_exists():
                    self._janela_calcular_quantidade.focus_force()
                    return
            except Exception:
                pass
        self._janela_calcular_quantidade = JanelaCalcularQuantidade(
            self,
            self._controlador,
            self._simbolo,
            ao_aplicar_quantidade=self._aplicar_quantidade_calculada,
        )

    def _aplicar_quantidade_calculada(self, quantidade: int) -> None:
        self._entrada_quantidade_cotas.delete(0, "end")
        self._entrada_quantidade_cotas.insert(0, formatar_inteiro_ptbr(quantidade))
        self._carregar_grafico()

    def _abrir_desvalorizacao(self) -> None:
        if self._janela_desvalorizacao is not None:
            try:
                if self._janela_desvalorizacao.winfo_exists():
                    self._janela_desvalorizacao.focus_force()
                    return
            except Exception:
                pass
        self._janela_desvalorizacao = JanelaDesvalorizacao(
            self,
            self._controlador,
            self._simbolo,
            periodo_chave=self._periodo_chave(),
            data_inicio=self._entrada_inicio.get(),
            data_fim=self._entrada_fim.get(),
        )

    def _abrir_mais_detalhes(self) -> None:
        from src.View.janela_detalhes_acao import JanelaDetalhesAcao

        if self._janela_detalhes is not None:
            try:
                if self._janela_detalhes.winfo_exists():
                    self._janela_detalhes.focus_force()
                    return
            except Exception:
                pass
        self._janela_detalhes = JanelaDetalhesAcao(self, self._controlador, self._simbolo)

    def _abrir_monitoramento(self) -> None:
        if self._janela_adicionar_monitoramento is not None:
            try:
                if self._janela_adicionar_monitoramento.winfo_exists():
                    self._janela_adicionar_monitoramento.focus_force()
                    self._janela_adicionar_monitoramento.lift()
                    return
            except Exception:
                pass

        tipo = inferir_tipo_ativo_monitoramento(self._simbolo, self._controlador)
        for item in self._controlador_monitoramento.listar_itens():
            if item.simbolo == self._simbolo and item.tipo_ativo == tipo:
                messagebox.showinfo(
                    "Monitoramento",
                    f"{codigo_exibicao(self._simbolo)} ja esta em monitoramento.\n"
                    "Abra a tela de monitoramento pelo icone de alerta no painel principal.",
                    parent=self,
                )
                return

        cotacao = self._painel_destaque_cotacao.cotacao_atual
        nome_ativo = cotacao.nome if cotacao else None
        preco_atual_texto = None
        preco_atual = None
        moeda_ativo = "BRL"
        if cotacao is not None:
            preco_atual = cotacao.preco
            moeda_ativo = cotacao.moeda
            preco = formatar_moeda(cotacao.preco, cotacao.moeda)
            variacao = formatar_variacao(
                cotacao.variacao_valor,
                cotacao.variacao_percentual,
                cotacao.moeda,
            )
            preco_atual_texto = f"{preco}  ({variacao})"

        def ao_salvar() -> None:
            messagebox.showinfo(
                "Monitoramento",
                f"{codigo_exibicao(self._simbolo)} adicionado ao monitoramento.",
                parent=self,
            )

        self._janela_adicionar_monitoramento = abrir_adicionar_monitoramento(
            self,
            self._controlador_monitoramento,
            ao_salvar,
            simbolo=self._simbolo,
            tipo_ativo=tipo,
            apenas_limites=True,
            nome_ativo=nome_ativo,
            preco_atual_texto=preco_atual_texto,
            preco_atual=preco_atual,
            moeda_ativo=moeda_ativo,
        )

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
        self._atualizar_rotulo_painel_periodo()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _atualizar_destaque_cotacao(self) -> None:
        iniciar_atualizacao_destaque(
            self._painel_destaque_cotacao,
            self._controlador,
            self._simbolo,
            self._executar_em_thread,
        )

    def _abrir_grafico_agora(self) -> None:
        janela = self._janela_grafico_agora
        if janela is not None:
            try:
                if janela.winfo_exists():
                    if getattr(janela, "_simbolo", None) == self._simbolo:
                        janela.focus_force()
                        janela.lift()
                        return
                    janela._ao_fechar()
            except Exception:
                pass

        self._label_status.configure(
            text="Abrindo tela Agora...",
            text_color=CORES["textoSecundario"],
        )
        self.after(50, self._criar_janela_grafico_agora)

    def _criar_janela_grafico_agora(self) -> None:
        if not self.winfo_exists():
            return
        self._janela_grafico_agora = abrir_grafico_tempo_real(
            self,
            self._controlador,
            self._simbolo,
        )

    def _abrir_blacklist(self) -> None:
        if self._janela_blacklist is not None:
            try:
                if self._janela_blacklist.winfo_exists():
                    self._janela_blacklist.focus_force()
                    return
            except Exception:
                pass

        self._janela_blacklist = abrir_blacklist_ativos(
            self,
            simbolo_sugerido=self._simbolo,
        )

    def _carregar_grafico(self) -> None:
        if self._carregando_grafico:
            return
        self._carregando_grafico = True
        self._manter_rolagem_no_topo()
        self._atualizar_destaque_cotacao()
        quantidade, erro_qtd = self._ler_quantidade_cotas()
        if erro_qtd:
            self._carregando_grafico = False
            self._label_status.configure(text=erro_qtd, text_color=CORES["erro"])
            return
        if quantidade is not None:
            try:
                self._config_ini.salvar_quantidade_cotas_grafico(quantidade)
            except OSError:
                self._carregando_grafico = False
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
            self._carregando_grafico = False
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

    def _alternar_modelo_grafico(self, modelo: ModeloGrafico) -> None:
        self._modelo_grafico = modelo
        self._redesenhar_grafico_em_cache()

    def _redesenhar_grafico_em_cache(self) -> None:
        dados = self._dados_grafico_atual
        if not dados:
            return
        self._desenhar_grafico(
            dados["labels"],
            dados["valores"],
            dados["titulo"],
            dados["simbolo"],
            dados["moeda"],
            dados["pontos_tooltip"],
            valores_cdi=dados.get("valores_cdi"),
        )

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
        if self._canvas is not None:
            try:
                self._canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self._canvas = None

        for widget in self._frame_grafico.winfo_children():
            widget.destroy()

        if self._figura:
            import matplotlib.pyplot as plt

            plt.close(self._figura)
            self._figura = None
            self._controle_zoom = None

        largura_px = max(400, self._frame_grafico.winfo_width() - 16)
        altura_px = max(350, ALTURA_GRAFICO_PX - 16)
        dpi = 100
        figura = Figure(
            figsize=(largura_px / dpi, altura_px / dpi),
            dpi=dpi,
            facecolor=CORES.get("graficoFundo", CORES["superficie"]),
        )
        eixo = figura.add_subplot(111)

        indices = np.arange(len(valores))
        linha = desenhar_serie_preco_principal(
            eixo,
            indices,
            valores,
            pontos_tooltip,
            modelo=self._modelo_grafico,
            cor=CORES["primaria"],
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
        configurar_rotulos_eixo_x(eixo, labels)
        eixo.grid(True, alpha=0.3, color=CORES["borda"])
        aplicar_tema_matplotlib(eixo, figura)
        figura.subplots_adjust(bottom=0.22, left=0.08, right=0.96, top=0.9)

        canvas = FigureCanvasTkAgg(figura, master=self._frame_grafico)

        def atualizar_painel(payload: dict) -> None:
            self._exibir_resumo_periodo(payload)

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
        self._exibir_resumo_periodo_do_grafico(
            canvas,
            pontos_tooltip,
            simbolo,
            moeda,
            atualizar_painel,
        )
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._figura = figura
        self._canvas = canvas
        self._controle_zoom = criar_controle_zoom(canvas, eixo)
        self._dados_grafico_atual = {
            "titulo": titulo,
            "labels": labels,
            "valores": valores,
            "simbolo": simbolo,
            "moeda": moeda,
            "pontos_tooltip": pontos_tooltip,
            "valores_cdi": valores_cdi,
            "modelo_grafico": self._modelo_grafico,
        }
        atualizar_estado_botao_grafico_ampliado(self._btn_grafico_ampliado, True)
        self.after(80, lambda: self._ajustar_grafico_ao_redimensionar(0))
        self.after(250, lambda: self._ajustar_grafico_ao_redimensionar(0))
        self._agendar_rolagem_no_topo()

    def _agendar_rolagem_no_topo(self) -> None:
        """Reaplica rolagem no topo apos pack/redraw do matplotlib."""
        self._manter_rolagem_no_topo()
        self.after_idle(self._manter_rolagem_no_topo)
        for atraso in (50, 120, 280, 450):
            self.after(atraso, self._manter_rolagem_no_topo)

    def _manter_rolagem_no_topo(self) -> None:
        """Mantem a area rolavel no inicio apos atualizar o grafico."""
        try:
            canvas = getattr(self._area_rolagem, "_parent_canvas", None)
            if canvas is not None:
                canvas.update_idletasks()
                canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _ajustar_grafico_ao_redimensionar(self, tentativa: int = 0) -> None:
        """Redimensiona o matplotlib apos a janela abrir maximizada."""
        if self._canvas is None or self._figura is None:
            if tentativa < 40:
                self.after(100, lambda: self._ajustar_grafico_ao_redimensionar(tentativa + 1))
            return
        try:
            self._frame_grafico.update_idletasks()
            largura_px = max(400, self._frame_grafico.winfo_width() - 16)
            altura_px = max(350, ALTURA_GRAFICO_PX - 16)
            if largura_px < 500 and tentativa < 40:
                self.after(100, lambda: self._ajustar_grafico_ao_redimensionar(tentativa + 1))
                return
            dpi = self._figura.get_dpi()
            self._figura.set_size_inches(largura_px / dpi, altura_px / dpi, forward=True)
            self._canvas.draw()
            self._manter_rolagem_no_topo()
        except Exception:
            pass

    def _exibir_resumo_periodo_do_grafico(
        self,
        canvas: FigureCanvasTkAgg,
        pontos: list[dict],
        simbolo: str,
        moeda: str,
        atualizar_painel,
    ) -> None:
        """Preenche o painel com o resumo do periodo inteiro exibido no grafico."""
        if len(pontos) < 2:
            return
        self._atualizar_rotulo_painel_periodo()
        quantidade = self._obter_quantidade_cotas_para_grafico()
        payload = calcular_comparacao_acao_unica(
            pontos,
            simbolo,
            moeda,
            0,
            len(pontos) - 1,
            quantidade,
        )
        _publicar_payload_com_cdi(canvas, payload, atualizar_painel)
