"""
Interface desktop 100% Python (CustomTkinter + Matplotlib).
Tela principal como hub de navegacao; cotacoes de acoes em tela dedicada.
"""

import customtkinter as ctk

from src.View.janela_hub_acoes import JanelaHubAcoes
from src.View.janela_hub_acoes_globais import JanelaHubAcoesGlobais
from src.View.janela_hub_criptomoedas import JanelaHubCriptomoedas
from src.View.janela_hub_fundos_imobiliarios import JanelaHubFundosImobiliarios
from src.View.janela_hub_etfs import JanelaHubEtfs
from src.View.janela_hub_tesouro import JanelaHubTesouro
from src.View.janela_hub_renda_fixa_bancaria import JanelaHubRendaFixaBancaria
from src.View.janela_hub_relatorios import JanelaHubRelatorios
from src.View.janela_configuracao_painel import (
    JanelaConfiguracaoPainel,
    ResultadoConfiguracaoPainel,
    abrir_configuracao_painel,
)
from src.View.janela_monitoramento import JanelaMonitoramento, abrir_monitoramento
from src.View.janela_carteira import JanelaCarteira, abrir_carteira
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.atualizacao_automatica_helper import (
    notificar_mudanca_configuracao_atualizacao_automatica,
)
from src.Tool.relatorio_automatico_helper import GerenciadorRelatorioAutomaticoCarteira
from src.Tool.relatorio_agendado_executor import ResultadoRelatorioAgendado
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
from src.View.tema import (
    CORES,
    aplicar_modo_aparencia,
)

class InterfaceApp(ctk.CTk):
    """Janela principal da aplicacao Financeiro."""

    def __init__(self) -> None:
        super().__init__()
        self._config_painel = ConfigPainelIni()
        self._janela_acoes: JanelaHubAcoes | None = None
        self._janela_acoes_globais: JanelaHubAcoesGlobais | None = None
        self._janela_cripto: JanelaHubCriptomoedas | None = None
        self._janela_fiis: JanelaHubFundosImobiliarios | None = None
        self._janela_etfs: JanelaHubEtfs | None = None
        self._janela_tesouro: JanelaHubTesouro | None = None
        self._janela_lci_lca: JanelaHubRendaFixaBancaria | None = None
        self._janela_cdb: JanelaHubRendaFixaBancaria | None = None
        self._janela_configuracao: JanelaConfiguracaoPainel | None = None
        self._janela_monitoramento: JanelaMonitoramento | None = None
        self._janela_carteira: JanelaCarteira | None = None
        self._janela_relatorios: JanelaHubRelatorios | None = None
        self._botao_alerta_monitoramento: ctk.CTkButton | None = None
        self._botao_monitoramento: ctk.CTkButton | None = None
        self._reconstruindo_tema = False

        self._configurar_aparencia()
        self._montar_layout()
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        # Abre maximizado no monitor salvo no INI (ou principal se ausente).
        configurar_janela_maximizada(
            self,
            monitor_inicial=self._config_painel.carregar_monitor_janela(),
            ao_salvar_monitor=self._salvar_monitor_principal,
        )
        self._gerenciador_relatorio_carteira = GerenciadorRelatorioAutomaticoCarteira(
            self,
            self._ao_concluir_relatorio_automatico_carteira,
            self._config_painel,
        )
        self._gerenciador_relatorio_carteira.iniciar()
        self.after(800, lambda: self._agendar_verificacao_alertas_monitoramento(notificar=True))

    def _salvar_monitor_principal(self, dispositivo: str) -> None:
        try:
            self._config_painel.salvar_monitor_janela(dispositivo)
        except OSError:
            pass

    def _ao_fechar(self) -> None:
        self._gerenciador_relatorio_carteira.parar()
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
            text="Escolha um mercado ou ferramenta. As cotacoes de acoes abrem na tela dedicada.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self._montar_area_consultas()

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

    def _abrir_hub_relatorios(self) -> None:
        """Abre (ou foca) o hub de relatorios (carteira e IPOs)."""
        if self._janela_relatorios is not None:
            try:
                if self._janela_relatorios.winfo_exists():
                    self._janela_relatorios.focus_force()
                    self._janela_relatorios.lift()
                    return
            except Exception:
                pass

        self._janela_relatorios = JanelaHubRelatorios(self)

    def _ao_concluir_relatorio_automatico_carteira(
        self,
        resultado: ResultadoRelatorioAgendado,
    ) -> None:
        """Atualiza status na carteira apos o executor gerar/enviar o relatorio."""
        if not widget_ainda_existe(self):
            return

        caminho = resultado.caminho_pdf
        if caminho is None:
            return

        opcoes = ConfigPainelIni().carregar_relatorio_automatico_carteira()
        qtd_emails = len(opcoes.emails_destinatarios)
        erro_email = resultado.mensagem if resultado.mensagem and "e-mail falhou" in resultado.mensagem.lower() else None

        texto_status = f"Relatorio automatico gerado: {caminho.name}"
        if erro_email:
            texto_status = f"{texto_status} | E-mail: {erro_email}"
        elif qtd_emails > 0:
            texto_status = (
                f"{texto_status} | E-mail enviado para {qtd_emails} destinatario(s)"
            )

        janela_carteira = self._janela_carteira
        if janela_carteira is None:
            return
        try:
            if not janela_carteira.winfo_exists():
                return
        except Exception:
            return

        cor_status = CORES["erro"] if erro_email else CORES["sucesso"]
        janela_carteira._label_status.configure(
            text=texto_status,
            text_color=cor_status,
        )

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

        if resultado.atualizacao_alterada:
            notificar_mudanca_configuracao_atualizacao_automatica()

    def _reconstruir_interface_apos_tema(self) -> None:
        """Remonta a tela principal para aplicar as novas cores."""
        self._reconstruindo_tema = True

        for widget in self.winfo_children():
            widget.destroy()

        self._janela_configuracao = None
        self.configure(fg_color=CORES["fundo"])
        self._montar_layout()

        self._reconstruindo_tema = False
        self.after(800, lambda: self._agendar_verificacao_alertas_monitoramento(notificar=False))

    def _montar_area_consultas(self) -> None:
        """Botoes de navegacao para mercados e ferramentas."""
        card_acao = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        card_acao.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        ctk.CTkLabel(
            card_acao,
            text="Consultas",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            card_acao,
            text="Abra o mercado desejado. Cotacoes e graficos de acoes ficam na tela Acoes.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=12, pady=(0, 8))

        linha_botoes = ctk.CTkFrame(card_acao, fg_color="transparent")
        linha_botoes.pack(fill="x", padx=12, pady=(0, 12))

        colunas = 4
        for indice_coluna in range(colunas):
            linha_botoes.grid_columnconfigure(indice_coluna, weight=1, uniform="consultas")

        botoes_consultas = [
            ("Acoes", self._abrir_hub_acoes),
            ("Acoes globais", self._abrir_hub_acoes_globais),
            ("Criptomoedas", self._abrir_hub_criptomoedas),
            ("Fundos imobiliarios", self._abrir_hub_fundos_imobiliarios),
            ("ETFs", self._abrir_hub_etfs),
            ("Tesouros", self._abrir_hub_tesouro),
            ("LCI/LCA", self._abrir_hub_lci_lca),
            ("CDB", self._abrir_hub_cdb),
            ("Carteira", self._abrir_carteira),
            ("Relatorios", self._abrir_hub_relatorios),
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

    def _abrir_hub_acoes(self) -> None:
        """Abre (ou foca) o painel dedicado de acoes da B3."""
        if self._janela_acoes is not None:
            try:
                if self._janela_acoes.winfo_exists():
                    self._janela_acoes.focus_force()
                    self._janela_acoes.lift()
                    return
            except Exception:
                pass

        self._janela_acoes = JanelaHubAcoes(self)

    def _abrir_hub_acoes_globais(self) -> None:
        """Abre (ou foca) o painel de BDRs (acoes globais na B3)."""
        if self._janela_acoes_globais is not None:
            try:
                if self._janela_acoes_globais.winfo_exists():
                    self._janela_acoes_globais.focus_force()
                    self._janela_acoes_globais.lift()
                    return
            except Exception:
                pass

        self._janela_acoes_globais = JanelaHubAcoesGlobais(self)

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

    def _abrir_hub_etfs(self) -> None:
        """Abre (ou foca) o painel de ETFs."""
        if self._janela_etfs is not None:
            try:
                if self._janela_etfs.winfo_exists():
                    self._janela_etfs.focus_force()
                    self._janela_etfs.lift()
                    return
            except Exception:
                pass

        self._janela_etfs = JanelaHubEtfs(self)

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


def iniciar_interface() -> None:
    """Abre a janela principal."""
    app = InterfaceApp()
    app.mainloop()
