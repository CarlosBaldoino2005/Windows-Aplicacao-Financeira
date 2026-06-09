"""
Interface desktop 100% Python (CustomTkinter + Matplotlib).
Painel, graficos e comparacao de acoes.
"""
import tkinter as tk
from tkinter import ttk

from src.View import mensagem_helper as messagebox

import customtkinter as ctk

from src.Controller.controlador_mercado import ControladorMercado
from src.Model.cotacao import CotacaoResumo
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.janela_comparar_acoes import JanelaCompararAcoes
from src.View.janela_noticias_mercado import JanelaNoticiasMercado
from src.View.janela_hub_criptomoedas import JanelaHubCriptomoedas
from src.View.janela_hub_empresas_dividendos import JanelaHubEmpresasDividendos
from src.View.janela_hub_fundos_imobiliarios import JanelaHubFundosImobiliarios
from src.View.janela_hub_painel_periodo import JanelaHubPainelPeriodo
from src.View.janela_hub_tesouro import JanelaHubTesouro
from src.View.janela_hub_renda_fixa_bancaria import JanelaHubRendaFixaBancaria
from src.View.janela_favoritas import JanelaFavoritas
from src.View.janela_pesquisa_acao import JanelaPesquisaAcao
from src.View.janela_configuracao_painel import (
    JanelaConfiguracaoPainel,
    ResultadoConfiguracaoPainel,
    abrir_configuracao_painel,
)
from src.View.janela_monitoramento import JanelaMonitoramento, abrir_monitoramento
from src.View.janela_carteira import JanelaCarteira, abrir_carteira
from src.View.tabela_mercado_helper import (
    criar_card_tabela,
    obter_simbolo_duplo_clique_treeview,
    preencher_tabela as preencher_tabela_mercado,
    reaplicar_fonte_em_tabelas,
)
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.atualizacao_automatica_helper import (
    GerenciadorAtualizacaoAutomatica,
    notificar_mudanca_configuracao_atualizacao_automatica,
)
from src.Tool.icone_engrenagem_helper import criar_botao_engrenagem
from src.Tool.icone_alerta_helper import criar_botao_alerta
from src.Tool.alerta_monitoramento_helper import (
    AlertaMonitoramentoItem,
    aplicar_destaque_alerta_ui,
    notificar_alertas_windows,
    obter_alertas_monitoramento,
    remover_destaque_alerta_ui,
    widget_ainda_existe,
)
from src.Tool.janela_helper import (
    configurar_janela_maximizada,
    executar_em_thread,
    obter_dispositivo_monitor_janela,
)
from src.Tool.validadores import validar_quantidade_acoes
from src.View.tema import (
    CORES,
    aplicar_modo_aparencia,
)

class InterfaceApp(ctk.CTk):
    """Janela principal da aplicacao Financeiro."""

    def __init__(self) -> None:
        super().__init__()
        self._controlador = ControladorMercado()
        self._config_painel = ConfigPainelIni()
        self._janela_pesquisa: JanelaPesquisaAcao | None = None
        self._janela_favoritas: JanelaFavoritas | None = None
        self._janela_comparar: JanelaCompararAcoes | None = None
        self._janela_noticias: JanelaNoticiasMercado | None = None
        self._janela_cripto: JanelaHubCriptomoedas | None = None
        self._janela_dividendos: JanelaHubEmpresasDividendos | None = None
        self._janela_fiis: JanelaHubFundosImobiliarios | None = None
        self._janela_painel_periodo: JanelaHubPainelPeriodo | None = None
        self._janela_tesouro: JanelaHubTesouro | None = None
        self._janela_lci_lca: JanelaHubRendaFixaBancaria | None = None
        self._janela_cdb: JanelaHubRendaFixaBancaria | None = None
        self._janela_grafico_acao: JanelaGraficoAcao | None = None
        self._janela_configuracao: JanelaConfiguracaoPainel | None = None
        self._janela_monitoramento: JanelaMonitoramento | None = None
        self._janela_carteira: JanelaCarteira | None = None
        self._botao_alerta_monitoramento: ctk.CTkButton | None = None
        self._botao_monitoramento: ctk.CTkButton | None = None
        self._carga_inicial_painel_feita = False
        self._reconstruindo_tema = False
        self._painel_buscando = False

        self._configurar_aparencia()
        self._montar_layout()
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        # Abre maximizado no monitor salvo no INI (ou principal se ausente).
        configurar_janela_maximizada(
            self,
            monitor_inicial=self._config_painel.carregar_monitor_janela(),
            ao_salvar_monitor=self._salvar_monitor_principal,
        )
        self._agendar_carga_inicial_painel()
        self._atualizador_auto = GerenciadorAtualizacaoAutomatica(
            self,
            self._config_painel,
            lambda: self._carregar_painel(automatico=True),
        )
        self._atualizador_auto.iniciar()
        self.after(800, lambda: self._agendar_verificacao_alertas_monitoramento(notificar=True))

    def _salvar_monitor_principal(self, dispositivo: str) -> None:
        try:
            self._config_painel.salvar_monitor_janela(dispositivo)
        except OSError:
            pass

    def _ao_fechar(self) -> None:
        self._atualizador_auto.parar()
        dispositivo = obter_dispositivo_monitor_janela(self)
        if dispositivo:
            self._salvar_monitor_principal(dispositivo)
        self.destroy()

    def _configurar_aparencia(self) -> None:
        aplicar_modo_aparencia(self._config_painel.carregar_modo_aparencia())
        self.title("Financeiro - Painel de Mercado")
        self.minsize(900, 600)
        self.configure(fg_color=CORES["fundo"])

    def _montar_layout(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x", padx=0, pady=0)

        linha_topo = ctk.CTkFrame(cabecalho, fg_color="transparent")
        linha_topo.pack(fill="x", padx=20, pady=(12, 0))

        ctk.CTkLabel(
            linha_topo,
            text="Financeiro",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")

        criar_botao_engrenagem(
            linha_topo,
            command=self._abrir_configuracao,
        ).pack(side="right")

        self._botao_alerta_monitoramento = criar_botao_alerta(
            linha_topo,
            command=self._abrir_monitoramento,
        )
        self._botao_alerta_monitoramento.pack(side="right", padx=(0, 6))

        ctk.CTkLabel(
            cabecalho,
            text="Cotacoes, acoes em alta e graficos para analise de investimentos",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self._montar_area_consultas()
        self._montar_secao_cotacoes()

        aviso = ctk.CTkLabel(
            self,
            text="Dados publicos (Yahoo Finance). Uso educacional — nao e recomendacao de investimento.",
            font=ctk.CTkFont(size=11),
            text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
            fg_color=CORES.get("destaqueAvisoLegal", CORES["avisoFundo"]),
            corner_radius=8,
        )
        aviso.pack(fill="x", padx=16, pady=(0, 12))

    def _abrir_configuracao(self) -> None:
        """Abre modal para tema, quantidade de acoes e fonte das grids."""
        if self._janela_configuracao is not None:
            try:
                if self._janela_configuracao.winfo_exists():
                    self._janela_configuracao.focus_force()
                    self._janela_configuracao.lift()
                    return
            except Exception:
                pass

        def ao_aplicar(resultado: ResultadoConfiguracaoPainel) -> None:
            self._processar_configuracao_painel(resultado)

        self._janela_configuracao = abrir_configuracao_painel(
            self, self._config_painel, ao_aplicar
        )

    def _abrir_carteira(self) -> None:
        if self._janela_carteira is not None:
            try:
                if self._janela_carteira.winfo_exists():
                    self._janela_carteira.focus_force()
                    self._janela_carteira.lift()
                    self._janela_carteira._atualizar_lista(forcar=True)
                    return
            except Exception:
                pass

        janela = abrir_carteira(self)
        self._janela_carteira = janela

    def _abrir_monitoramento(self) -> None:
        if self._janela_monitoramento is not None:
            try:
                if self._janela_monitoramento.winfo_exists():
                    self._janela_monitoramento.focus_force()
                    self._janela_monitoramento.lift()
                    self._janela_monitoramento._atualizar_lista(forcar=True)
                    return
            except Exception:
                pass

        janela = abrir_monitoramento(self)
        self._janela_monitoramento = janela
        if janela is not None:
            janela.bind(
                "<Destroy>",
                lambda _e: self._agendar_verificacao_alertas_monitoramento(notificar=False),
                add="+",
            )

    def _agendar_verificacao_alertas_monitoramento(self, *, notificar: bool = False) -> None:
        """Consulta limites do monitoramento e atualiza icone/botao (e notificacoes na abertura)."""
        if not widget_ainda_existe(self):
            return

        def trabalho() -> tuple[list[AlertaMonitoramentoItem], bool]:
            return obter_alertas_monitoramento()

        def ao_concluir(
            resultado: tuple[list[AlertaMonitoramentoItem], bool] | None,
            erro: str | None,
        ) -> None:
            if erro or resultado is None:
                return
            alertas, monitoramento_ativo = resultado
            self._aplicar_indicadores_alerta_monitoramento(alertas, monitoramento_ativo)
            if notificar and monitoramento_ativo and alertas:
                notificar_alertas_windows(alertas)

        self._executar_em_thread(trabalho, ao_concluir)

    def _aplicar_indicadores_alerta_monitoramento(
        self,
        alertas: list[AlertaMonitoramentoItem],
        monitoramento_ativo: bool,
    ) -> None:
        if not widget_ainda_existe(self):
            return

        if monitoramento_ativo and alertas:
            aplicar_destaque_alerta_ui(
                self._botao_alerta_monitoramento,
                self._botao_monitoramento,
            )
            return

        remover_destaque_alerta_ui(
            self._botao_alerta_monitoramento,
            self._botao_monitoramento,
        )

    def _processar_configuracao_painel(self, resultado: ResultadoConfiguracaoPainel) -> None:
        if resultado.tema_alterado:
            aplicar_modo_aparencia(resultado.modo_aparencia)
            self._reconstruir_interface_apos_tema()
            if resultado.atualizacao_alterada:
                notificar_mudanca_configuracao_atualizacao_automatica()
            return

        if resultado.quantidade_alterada:
            self._carregar_painel()
        elif resultado.fonte_alterada:
            self._ao_mudar_fonte_grid()

        if resultado.atualizacao_alterada:
            notificar_mudanca_configuracao_atualizacao_automatica()

    def _reconstruir_interface_apos_tema(self) -> None:
        """Remonta a tela principal para aplicar as novas cores."""
        self._reconstruindo_tema = True
        recarregar_painel = self._carga_inicial_painel_feita

        for widget in self.winfo_children():
            widget.destroy()

        self._carga_inicial_painel_feita = False
        self._janela_configuracao = None
        self.configure(fg_color=CORES["fundo"])
        self._montar_layout()

        if recarregar_painel:
            self._carregar_painel()
        else:
            self._agendar_carga_inicial_painel()

        self._reconstruindo_tema = False
        self._atualizador_auto.reagendar()
        self.after(800, lambda: self._agendar_verificacao_alertas_monitoramento(notificar=False))

    def _montar_area_consultas(self) -> None:
        """Botoes de pesquisa e favoritos acima das abas de cotacoes."""
        card_acao = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        card_acao.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            card_acao,
            text="Consultas",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            card_acao,
            text="Pesquise acoes, favoritos, comparacao e noticias do mercado em telas dedicadas.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=12, pady=(0, 8))

        linha_botoes = ctk.CTkFrame(card_acao, fg_color="transparent")
        linha_botoes.pack(fill="x", padx=12, pady=(0, 8))

        colunas = 4
        for indice_coluna in range(colunas):
            linha_botoes.grid_columnconfigure(indice_coluna, weight=1, uniform="consultas")

        botoes_consultas = [
            ("Pesquisar acao", self._abrir_janela_pesquisa_acao),
            ("Acoes favoritas", self._abrir_janela_favoritas),
            ("Comparar acoes", self._abrir_janela_comparar_acoes),
            ("Noticias do mercado", self._abrir_janela_noticias),
            ("Criptomoedas", self._abrir_hub_criptomoedas),
            ("Empresa + dividendos", self._abrir_hub_empresas_dividendos),
            ("Fundos imobiliarios", self._abrir_hub_fundos_imobiliarios),
            ("Acoes por periodo", self._abrir_hub_painel_periodo),
            ("Tesouros", self._abrir_hub_tesouro),
            ("LCI/LCA", self._abrir_hub_lci_lca),
            ("CDB", self._abrir_hub_cdb),
            ("Carteira", self._abrir_carteira),
            ("Monitoramento", self._abrir_monitoramento),
        ]

        for indice, (rotulo, acao) in enumerate(botoes_consultas):
            botao = ctk.CTkButton(
                linha_botoes,
                text=rotulo,
                command=acao,
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
                height=36,
            )
            if rotulo == "Monitoramento":
                self._botao_monitoramento = botao
            botao.grid(
                row=indice // colunas,
                column=indice % colunas,
                padx=(0, 10),
                pady=(0, 8),
                sticky="ew",
            )

        barra = ctk.CTkFrame(card_acao, fg_color="transparent")
        barra.pack(fill="x", padx=12, pady=(0, 12))

        qtd_ini = self._config_painel.carregar()
        self._label_status_painel = ctk.CTkLabel(
            barra,
            text=f"Carregando ate {qtd_ini} acoes em cada aba...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status_painel.pack(side="left")

        ctk.CTkButton(
            barra,
            text="Atualizar cotacoes",
            command=self._carregar_painel,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(side="right")

    def _montar_secao_cotacoes(self) -> None:
        """Abas Em alta / Em queda / Todas sem CTkTabview (evita conteudo empilhado e oculto)."""
        self._secao_cotacoes = ctk.CTkFrame(self, fg_color=CORES["fundo"])
        self._secao_cotacoes.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._seletor_aba_cot = ctk.CTkSegmentedButton(
            self._secao_cotacoes,
            values=["Em alta", "Em queda", "Todas"],
            command=self._trocar_aba_cotacoes,
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            selected_hover_color=CORES["primariaHover"],
            unselected_color=CORES["superficie"],
            unselected_hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        )
        self._seletor_aba_cot.pack(fill="x", padx=4, pady=(8, 6))

        self._container_aba_cot = ctk.CTkFrame(self._secao_cotacoes, fg_color="transparent")
        self._container_aba_cot.pack(fill="both", expand=True)

        self._aba_alta = ctk.CTkFrame(self._container_aba_cot, fg_color=CORES["fundo"])
        self._aba_queda = ctk.CTkFrame(self._container_aba_cot, fg_color=CORES["fundo"])
        self._aba_todas = ctk.CTkFrame(self._container_aba_cot, fg_color=CORES["fundo"])

        self._montar_abas_cotacoes()
        self._trocar_aba_cotacoes("Em alta")

    def _trocar_aba_cotacoes(self, nome_aba: str) -> None:
        for frame in (self._aba_alta, self._aba_queda, self._aba_todas):
            frame.pack_forget()
        destino = {
            "Em alta": self._aba_alta,
            "Em queda": self._aba_queda,
            "Todas": self._aba_todas,
        }.get(nome_aba, self._aba_alta)
        destino.pack(fill="both", expand=True)

    def _montar_conteudo_aba_cotacoes(
        self, aba: ctk.CTkFrame, titulo: str
    ) -> ttk.Treeview:
        """Container fixo na aba evita grid sumir no CTkTabview."""
        container = ctk.CTkFrame(aba, fg_color=CORES["fundo"])
        container.pack(fill="both", expand=True, padx=4, pady=4)

        scroll = ctk.CTkScrollableFrame(container, fg_color=CORES["fundo"])
        scroll.pack(fill="both", expand=True)

        return criar_card_tabela(
            scroll,
            titulo,
            altura=14,
            ao_duplo_clique=self._ao_duplo_clique_tabela,
            expandir=True,
        )

    def _montar_abas_cotacoes(self) -> None:
        """Uma aba para cada lista: alta, queda e todas."""
        self._tabela_alta = self._montar_conteudo_aba_cotacoes(
            self._aba_alta,
            "Acoes em alta no dia (duplo clique abre o grafico)",
        )
        self._tabela_queda = self._montar_conteudo_aba_cotacoes(
            self._aba_queda,
            "Acoes em queda no dia (duplo clique abre o grafico)",
        )
        self._tabela_todas = self._montar_conteudo_aba_cotacoes(
            self._aba_todas,
            "Todas as acoes monitoradas (duplo clique abre o grafico)",
        )

    def _agendar_carga_inicial_painel(self) -> None:
        """Carrega alta, queda e todas automaticamente ao abrir o sistema."""
        self.after(150, self._executar_carga_inicial_painel)
        self.bind("<Map>", self._ao_janela_exibida, add=True)

    def _ao_janela_exibida(self, _evento=None) -> None:
        self._executar_carga_inicial_painel()

    def _executar_carga_inicial_painel(self) -> None:
        if self._carga_inicial_painel_feita:
            return
        if not self.winfo_exists():
            return
        self._carga_inicial_painel_feita = True
        self._carregar_painel()

    def _preencher_tabela(
        self,
        tabela: ttk.Treeview,
        itens: list[CotacaoResumo],
        mensagem_vazio: str | None = None,
    ) -> None:
        preencher_tabela_mercado(tabela, itens, mensagem_vazio)

    def _ao_mudar_fonte_grid(self) -> None:
        """Reaplica tamanho da fonte nas tres abas do painel (valor salvo no INI)."""
        tabelas = [
            getattr(self, "_tabela_alta", None),
            getattr(self, "_tabela_queda", None),
            getattr(self, "_tabela_todas", None),
        ]
        reaplicar_fonte_em_tabelas(t for t in tabelas if t is not None)

    def _ao_duplo_clique_tabela(self, evento) -> None:
        simbolo = obter_simbolo_duplo_clique_treeview(evento.widget, evento)
        if not simbolo:
            return
        self._abrir_grafico_por_simbolo(simbolo)

    def _abrir_grafico_por_simbolo(self, simbolo: str) -> None:
        """Abre janela dedicada com grafico da acao (duplo clique no painel)."""
        if self._janela_grafico_acao is not None:
            try:
                if self._janela_grafico_acao.winfo_exists():
                    self._janela_grafico_acao._ao_fechar()
            except Exception:
                pass

        self._janela_grafico_acao = JanelaGraficoAcao(self, self._controlador, simbolo)

    def _abrir_janela_pesquisa_acao(self) -> None:
        """Abre (ou foca) a tela dedicada de pesquisa de acao."""
        if self._janela_pesquisa is not None:
            try:
                if self._janela_pesquisa.winfo_exists():
                    self._janela_pesquisa.focus_force()
                    self._janela_pesquisa.lift()
                    return
            except Exception:
                pass

        self._janela_pesquisa = JanelaPesquisaAcao(self, self._controlador)

    def _abrir_janela_favoritas(self) -> None:
        """Abre (ou foca) a tela de acoes favoritas."""
        if self._janela_favoritas is not None:
            try:
                if self._janela_favoritas.winfo_exists():
                    self._janela_favoritas.focus_force()
                    self._janela_favoritas.lift()
                    self._janela_favoritas._atualizar_grid()
                    return
            except Exception:
                pass

        self._janela_favoritas = JanelaFavoritas(self, self._controlador)

    def _abrir_janela_comparar_acoes(self) -> None:
        """Abre (ou foca) a tela dedicada de comparacao de acoes."""
        if self._janela_comparar is not None:
            try:
                if self._janela_comparar.winfo_exists():
                    self._janela_comparar.focus_force()
                    self._janela_comparar.lift()
                    return
            except Exception:
                pass

        self._janela_comparar = JanelaCompararAcoes(self, self._controlador)

    def _abrir_janela_noticias(self) -> None:
        """Abre (ou foca) a tela de noticias do mercado."""
        if self._janela_noticias is not None:
            try:
                if self._janela_noticias.winfo_exists():
                    self._janela_noticias.focus_force()
                    self._janela_noticias.lift()
                    return
            except Exception:
                pass

        self._janela_noticias = JanelaNoticiasMercado(self, self._controlador)

    def _abrir_hub_criptomoedas(self) -> None:
        """Abre (ou foca) o painel dedicado de criptomoedas."""
        if self._janela_cripto is not None:
            try:
                if self._janela_cripto.winfo_exists():
                    self._janela_cripto.focus_force()
                    self._janela_cripto.lift()
                    return
            except Exception:
                pass

        self._janela_cripto = JanelaHubCriptomoedas(self)

    def _abrir_hub_empresas_dividendos(self) -> None:
        """Abre (ou foca) o painel de empresas que pagam dividendos."""
        if self._janela_dividendos is not None:
            try:
                if self._janela_dividendos.winfo_exists():
                    self._janela_dividendos.focus_force()
                    self._janela_dividendos.lift()
                    return
            except Exception:
                pass

        self._janela_dividendos = JanelaHubEmpresasDividendos(self)

    def _abrir_hub_fundos_imobiliarios(self) -> None:
        """Abre (ou foca) o painel de fundos imobiliarios (FIIs)."""
        if self._janela_fiis is not None:
            try:
                if self._janela_fiis.winfo_exists():
                    self._janela_fiis.focus_force()
                    self._janela_fiis.lift()
                    return
            except Exception:
                pass

        self._janela_fiis = JanelaHubFundosImobiliarios(self)

    def _abrir_hub_painel_periodo(self) -> None:
        """Abre painel em alta / queda / todas com variacao no periodo escolhido."""
        if self._janela_painel_periodo is not None:
            try:
                if self._janela_painel_periodo.winfo_exists():
                    self._janela_painel_periodo.focus_force()
                    self._janela_painel_periodo.lift()
                    return
            except Exception:
                pass

        self._janela_painel_periodo = JanelaHubPainelPeriodo(self)

    def _abrir_hub_tesouro(self) -> None:
        """Abre (ou foca) o painel do Tesouro Direto."""
        if self._janela_tesouro is not None:
            try:
                if self._janela_tesouro.winfo_exists():
                    self._janela_tesouro.focus_force()
                    self._janela_tesouro.lift()
                    return
            except Exception:
                pass

        self._janela_tesouro = JanelaHubTesouro(self)

    def _abrir_hub_lci_lca(self) -> None:
        """Abre (ou foca) o painel de LCI e LCA."""
        if self._janela_lci_lca is not None:
            try:
                if self._janela_lci_lca.winfo_exists():
                    self._janela_lci_lca.focus_force()
                    self._janela_lci_lca.lift()
                    return
            except Exception:
                pass
        self._janela_lci_lca = JanelaHubRendaFixaBancaria(self, modo="lci_lca")

    def _abrir_hub_cdb(self) -> None:
        """Abre (ou foca) o painel de CDB."""
        if self._janela_cdb is not None:
            try:
                if self._janela_cdb.winfo_exists():
                    self._janela_cdb.focus_force()
                    self._janela_cdb.lift()
                    return
            except Exception:
                pass
        self._janela_cdb = JanelaHubRendaFixaBancaria(self, modo="cdb")

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
            messagebox.showwarning("Quantidade", erro_qtd)
            return

        if not automatico:
            try:
                self._config_painel.salvar(quantidade)
            except OSError:
                messagebox.showwarning(
                    "Configuracao",
                    "Nao foi possivel salvar dados/painel.ini. As cotacoes serao atualizadas mesmo assim.",
                )

        self._painel_buscando = True
        self._label_status_painel.configure(
            text=f"Carregando ate {quantidade} acoes em cada aba..."
        )

        def buscar():
            return self._controlador.obter_painel(quantidade)

        def ao_concluir(dados, erro):
            self._painel_buscando = False
            if erro:
                self._label_status_painel.configure(text=f"Erro: {erro}", text_color=CORES["erro"])
                if not automatico:
                    messagebox.showerror("Erro", erro)
                return
            self._preencher_tabela(
                self._tabela_alta,
                dados["em_alta"],
                (
                    "Nenhuma acao com variacao positiva no dia neste momento. "
                    "Veja a aba Todas ou atualize as cotacoes mais tarde."
                ),
            )
            self._preencher_tabela(
                self._tabela_queda,
                dados["em_queda"],
                "Nenhuma acao com variacao negativa no dia neste momento.",
            )
            self._preencher_tabela(self._tabela_todas, dados["todas"])
            self._trocar_aba_cotacoes("Em alta")
            if hasattr(self, "_seletor_aba_cot"):
                self._seletor_aba_cot.set("Em alta")
            self.update_idletasks()
            qtd = dados.get("quantidade", quantidade)
            qtd_alta = len(dados["em_alta"])
            texto_status = (
                f"Atualizado em {self._hora_agora()} — limite {qtd} | "
                f"alta {qtd_alta} | "
                f"baixa {len(dados['em_queda'])} | "
                f"todas {len(dados['todas'])}"
            )
            if qtd_alta == 0:
                texto_status += " | Em alta: nenhuma cotacao positiva agora"
            self._label_status_painel.configure(
                text=texto_status,
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    @staticmethod
    def _hora_agora() -> str:
        from datetime import datetime

        return datetime.now().strftime("%H:%M:%S")


def iniciar_interface() -> None:
    """Abre a janela principal."""
    app = InterfaceApp()
    app.mainloop()
