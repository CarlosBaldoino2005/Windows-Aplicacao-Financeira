"""Hub de acoes da B3 (alta, queda, todas e consultas dedicadas)."""
from __future__ import annotations

from datetime import datetime
from tkinter import ttk

from src.View import mensagem_helper as messagebox

import customtkinter as ctk

from src.Controller.controlador_mercado import ControladorMercado
from src.Model.cotacao import CotacaoResumo
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.atualizacao_automatica_helper import GerenciadorAtualizacaoAutomatica
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.Tool.validadores import validar_quantidade_acoes
from src.View.hub_painel_config_helper import ConfiguracaoHubPainel
from src.View.janela_comparar_acoes import JanelaCompararAcoes
from src.View.janela_favoritas import JanelaFavoritas
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.janela_grafico_tempo_real import JanelaGraficoTempoReal
from src.View.hub_agora_helper import abrir_agora_da_selecao_grid, obter_tabela_aba_ativa
from src.View.janela_hub_empresas_dividendos import JanelaHubEmpresasDividendos
from src.View.janela_hub_painel_periodo import JanelaHubPainelPeriodo
from src.View.janela_noticias_mercado import JanelaNoticiasMercado
from src.View.janela_pesquisa_acao import JanelaPesquisaAcao
from src.View.tabela_mercado_helper import (
    criar_card_tabela,
    obter_simbolo_duplo_clique_treeview,
    preencher_tabela as preencher_tabela_mercado,
    reaplicar_fonte_em_tabelas,
)
from src.View.tema import CORES


class JanelaHubAcoes(ctk.CTkToplevel):
    """Painel dedicado a acoes da B3 com cotacoes do dia e consultas."""

    def __init__(self, pai: ctk.CTk) -> None:
        super().__init__(pai)
        self._controlador = ControladorMercado()
        self._config_painel = ConfigPainelIni()
        self._janela_pesquisa: JanelaPesquisaAcao | None = None
        self._janela_favoritas: JanelaFavoritas | None = None
        self._janela_comparar: JanelaCompararAcoes | None = None
        self._janela_noticias: JanelaNoticiasMercado | None = None
        self._janela_grafico: JanelaGraficoAcao | None = None
        self._janela_grafico_agora: JanelaGraficoTempoReal | None = None
        self._janela_periodo: JanelaHubPainelPeriodo | None = None
        self._janela_dividendos: JanelaHubEmpresasDividendos | None = None
        self._carga_inicial_feita = False
        self._painel_buscando = False
        self._atualizador_auto = None
        self._config_hub = ConfiguracaoHubPainel(
            self,
            self._config_painel,
            escopo_quantidade="acoes",
            ao_recarregar=lambda: self._carregar_painel(),
            ao_mudar_fonte=self._ao_mudar_fonte_grid,
            ao_remontar_layout=self._reconstruir_interface_apos_tema,
            ao_reagendar_auto=self._reagendar_atualizacao_automatica,
        )

        self.title("Acoes")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 600)

        self._montar_layout()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(200, self._executar_carga_inicial)
        self._atualizador_auto = GerenciadorAtualizacaoAutomatica(
            self,
            self._config_painel,
            lambda: self._carregar_painel(automatico=True),
        )
        self._atualizador_auto.iniciar()

    def _ao_fechar(self) -> None:
        self._atualizador_auto.parar()
        for attr in (
            "_janela_pesquisa",
            "_janela_favoritas",
            "_janela_comparar",
            "_janela_noticias",
            "_janela_grafico",
            "_janela_grafico_agora",
            "_janela_periodo",
            "_janela_dividendos",
        ):
            janela = getattr(self, attr, None)
            if janela is not None:
                try:
                    if janela.winfo_exists():
                        if hasattr(janela, "_ao_fechar"):
                            janela._ao_fechar()
                        else:
                            janela.destroy()
                except Exception:
                    pass
        self.destroy()

    def _montar_layout(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        self._config_hub.montar_titulo_com_engrenagem(cabecalho, "Acoes")

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Cotacoes do dia, pesquisa, favoritos, comparacao e variacao por periodo. "
                "Duplo clique na grid abre o grafico."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self._montar_consultas()
        self._montar_painel_cotacoes()

        ctk.CTkLabel(
            self,
            text="Dados publicos (Yahoo Finance). Uso educacional — nao e recomendacao de investimento.",
            font=ctk.CTkFont(size=11),
            text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
            fg_color=CORES.get("destaqueAvisoLegal", CORES["avisoFundo"]),
            corner_radius=8,
        ).pack(fill="x", padx=16, pady=(0, 12))

    def _montar_consultas(self) -> None:
        card = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        card.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            card,
            text="Consultas",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            card,
            text="Pesquise tickers, favoritos, comparacao, dividendos e variacao por periodo.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=12, pady=(0, 8))

        linha = ctk.CTkFrame(card, fg_color="transparent")
        linha.pack(anchor="w", padx=12, pady=(0, 8))

        for texto, comando in (
            ("Pesquisar acao", self._abrir_pesquisa),
            ("Acoes favoritas", self._abrir_favoritas),
            ("Comparar acoes", self._abrir_comparar),
            ("Noticias do mercado", self._abrir_noticias),
            ("Acoes por periodo", self._abrir_por_periodo),
            ("Empresa + dividendos", self._abrir_empresas_dividendos),
        ):
            ctk.CTkButton(
                linha,
                text=texto,
                command=comando,
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=170,
                height=36,
            ).pack(side="left", padx=(0, 8))

        barra = ctk.CTkFrame(card, fg_color="transparent")
        barra.pack(fill="x", padx=12, pady=(0, 12))

        qtd = self._config_painel.carregar()
        self._label_status = ctk.CTkLabel(
            barra,
            text=f"Carregando ate {qtd} acoes em cada aba...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(side="left")

        ctk.CTkButton(
            barra,
            text="Agora",
            command=self._abrir_grafico_agora,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=90,
        ).pack(side="right", padx=(0, 8))

        ctk.CTkButton(
            barra,
            text="Atualizar cotacoes",
            command=self._carregar_painel,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(side="right")

    def _reagendar_atualizacao_automatica(self) -> None:
        if self._atualizador_auto is not None:
            self._atualizador_auto.reagendar()

    def _reconstruir_interface_apos_tema(self) -> None:
        recarregar = self._carga_inicial_feita
        for widget in self.winfo_children():
            widget.destroy()
        self._carga_inicial_feita = False
        self._config_hub.limpar_referencia_modal()
        self.configure(fg_color=CORES["fundo"])
        self._montar_layout()
        if recarregar:
            self._carregar_painel()
        else:
            self.after(200, self._executar_carga_inicial)
        self._reagendar_atualizacao_automatica()

    def _montar_painel_cotacoes(self) -> None:
        secao = ctk.CTkFrame(self, fg_color=CORES["fundo"])
        secao.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._seletor_abas = ctk.CTkSegmentedButton(
            secao,
            values=["Em alta", "Em queda", "Todas"],
            command=self._trocar_aba,
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            selected_hover_color=CORES["primariaHover"],
            unselected_color=CORES["superficie"],
            unselected_hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        )
        self._seletor_abas.pack(fill="x", padx=4, pady=(8, 6))

        container = ctk.CTkFrame(secao, fg_color="transparent")
        container.pack(fill="both", expand=True)

        self._aba_alta = ctk.CTkFrame(container, fg_color=CORES["fundo"])
        self._aba_queda = ctk.CTkFrame(container, fg_color=CORES["fundo"])
        self._aba_todas = ctk.CTkFrame(container, fg_color=CORES["fundo"])

        self._tabela_alta = self._criar_tabela_aba(
            self._aba_alta,
            "Acoes em alta no dia (duplo clique abre o grafico)",
        )
        self._tabela_queda = self._criar_tabela_aba(
            self._aba_queda,
            "Acoes em queda no dia (duplo clique abre o grafico)",
        )
        self._tabela_todas = self._criar_tabela_aba(
            self._aba_todas,
            "Todas as acoes monitoradas (duplo clique abre o grafico)",
        )
        self._trocar_aba("Em alta")

    def _criar_tabela_aba(self, aba: ctk.CTkFrame, titulo: str) -> ttk.Treeview:
        frame = ctk.CTkFrame(aba, fg_color=CORES["fundo"])
        frame.pack(fill="both", expand=True, padx=4, pady=4)
        scroll = ctk.CTkScrollableFrame(frame, fg_color=CORES["fundo"])
        scroll.pack(fill="both", expand=True)
        return criar_card_tabela(
            scroll,
            titulo,
            altura=14,
            ao_duplo_clique=self._ao_duplo_clique,
            expandir=True,
        )

    def _trocar_aba(self, nome: str) -> None:
        for frame in (self._aba_alta, self._aba_queda, self._aba_todas):
            frame.pack_forget()
        destino = {
            "Em alta": self._aba_alta,
            "Em queda": self._aba_queda,
            "Todas": self._aba_todas,
        }.get(nome, self._aba_alta)
        destino.pack(fill="both", expand=True)

    def _executar_carga_inicial(self) -> None:
        if self._carga_inicial_feita or not self.winfo_exists():
            return
        self._carga_inicial_feita = True
        self._carregar_painel()

    def _abrir_pesquisa(self) -> None:
        if self._focar_janela(self._janela_pesquisa):
            return
        self._janela_pesquisa = JanelaPesquisaAcao(self, self._controlador)

    def _abrir_favoritas(self) -> None:
        if self._focar_janela(self._janela_favoritas):
            self._janela_favoritas._atualizar_grid()
            return
        self._janela_favoritas = JanelaFavoritas(self, self._controlador, tipo_painel="acoes")

    def _abrir_comparar(self) -> None:
        if self._focar_janela(self._janela_comparar):
            return
        self._janela_comparar = JanelaCompararAcoes(self, self._controlador)

    def _abrir_noticias(self) -> None:
        if self._focar_janela(self._janela_noticias):
            return
        self._janela_noticias = JanelaNoticiasMercado(self, self._controlador)

    def _abrir_por_periodo(self) -> None:
        if self._focar_janela(self._janela_periodo):
            return
        self._janela_periodo = JanelaHubPainelPeriodo(self)

    def _abrir_empresas_dividendos(self) -> None:
        if self._focar_janela(self._janela_dividendos):
            return
        self._janela_dividendos = JanelaHubEmpresasDividendos(self)

    @staticmethod
    def _focar_janela(janela) -> bool:
        if janela is None:
            return False
        try:
            if janela.winfo_exists():
                janela.focus_force()
                janela.lift()
                return True
        except Exception:
            pass
        return False

    def _ao_duplo_clique(self, evento) -> None:
        simbolo = obter_simbolo_duplo_clique_treeview(evento.widget, evento)
        if not simbolo:
            return
        self._abrir_grafico(simbolo)

    def _abrir_grafico(self, simbolo: str) -> None:
        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass
        self._janela_grafico = JanelaGraficoAcao(self, self._controlador, simbolo)
        codigo = simbolo.replace(".SA", "")
        self._janela_grafico.title(f"Grafico — {codigo}")

    def _obter_tabela_ativa(self) -> ttk.Treeview | None:
        return obter_tabela_aba_ativa(
            self._seletor_abas.get(),
            {
                "Em alta": self._tabela_alta,
                "Em queda": self._tabela_queda,
                "Todas": self._tabela_todas,
            },
            padrao="Em alta",
        )

    def _abrir_grafico_agora(self) -> None:
        self._janela_grafico_agora = abrir_agora_da_selecao_grid(
            self,
            self._controlador,
            self._obter_tabela_ativa(),
            self._janela_grafico_agora,
        )

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _ler_quantidade_painel(self) -> tuple[int | None, str | None]:
        return validar_quantidade_acoes(str(self._config_painel.carregar()))

    def _carregar_painel(self, automatico: bool = False) -> None:
        if automatico and self._painel_buscando:
            return

        if automatico:
            quantidade = self._config_painel.carregar()
            erro_qtd = None
        else:
            quantidade, erro_qtd = self._ler_quantidade_painel()
        if erro_qtd:
            messagebox.showwarning("Quantidade", erro_qtd, parent=self)
            return

        if not automatico:
            try:
                self._config_painel.salvar(quantidade)
            except OSError:
                messagebox.showwarning(
                    "Configuracao",
                    "Nao foi possivel salvar dados/painel.ini. As cotacoes serao atualizadas mesmo assim.",
                    parent=self,
                )

        self._painel_buscando = True
        self._label_status.configure(
            text=f"Carregando ate {quantidade} acoes em cada aba..."
        )

        def buscar():
            return self._controlador.obter_painel(quantidade)

        def ao_concluir(dados, erro):
            self._painel_buscando = False
            if erro:
                self._label_status.configure(text=f"Erro: {erro}", text_color=CORES["erro"])
                if not automatico:
                    messagebox.showerror("Erro", erro, parent=self)
                return
            self._preencher(
                self._tabela_alta,
                dados["em_alta"],
                (
                    "Nenhuma acao com variacao positiva no dia neste momento. "
                    "Veja a aba Todas ou atualize as cotacoes mais tarde."
                ),
            )
            self._preencher(
                self._tabela_queda,
                dados["em_queda"],
                "Nenhuma acao com variacao negativa no dia neste momento.",
            )
            self._preencher(self._tabela_todas, dados["todas"])
            self._trocar_aba("Em alta")
            self._seletor_abas.set("Em alta")
            hora = datetime.now().strftime("%H:%M:%S")
            qtd = dados.get("quantidade", quantidade)
            texto_status = (
                f"Atualizado as {hora} — limite {qtd} | "
                f"alta {len(dados['em_alta'])} | "
                f"baixa {len(dados['em_queda'])} | "
                f"todas {len(dados['todas'])}"
            )
            if len(dados["em_alta"]) == 0:
                texto_status += " | Em alta: nenhuma cotacao positiva agora"
            self._label_status.configure(
                text=texto_status,
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _ao_mudar_fonte_grid(self) -> None:
        reaplicar_fonte_em_tabelas(
            [
                getattr(self, "_tabela_alta", None),
                getattr(self, "_tabela_queda", None),
                getattr(self, "_tabela_todas", None),
            ]
        )

    def _preencher(
        self,
        tabela: ttk.Treeview,
        itens: list[CotacaoResumo],
        mensagem_vazio: str | None = None,
    ) -> None:
        preencher_tabela_mercado(tabela, itens, mensagem_vazio)
