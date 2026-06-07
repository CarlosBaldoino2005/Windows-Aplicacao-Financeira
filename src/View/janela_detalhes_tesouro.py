"""Detalhes educativos de um titulo do Tesouro Direto."""
from __future__ import annotations

import webbrowser

import customtkinter as ctk
from tkinter import messagebox

from src.Controller.controlador_tesouro import ControladorTesouro
from src.Model.simulacao_tesouro import ResultadoSimulacaoTesouro
from src.Model.tesouro_informacoes import InformacoesFamiliaTesouro
from src.Model.titulo_tesouro import DetalhesTituloTesouro
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr
from src.View.formatadores import formatar_moeda, formatar_texto_opcional
from src.View.tabela_detalhes_helper import adicionar_cabecalho_tabela, adicionar_linha_zebrada
from src.View.tema import CORES

NOMES_ABAS = ("Cotacao", "Simular", "Caracteristicas", "Impostos", "Historico PU")


class JanelaDetalhesTesouro(ctk.CTkToplevel):
    """Tela com cotacao, volatilidade indicativa, liquidez e guia por familia."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: ControladorTesouro,
        identificador: str,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._identificador = identificador
        self._detalhes: DetalhesTituloTesouro | None = None
        self._frames_por_aba: dict[str, ctk.CTkFrame] = {}
        self._container_abas: ctk.CTkFrame | None = None
        self._frame_resultado_simulacao: ctk.CTkFrame | None = None
        self._entrada_valor_simulacao: ctk.CTkEntry | None = None

        self.title("Detalhes — Tesouro Direto")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(880, 600)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()
        self.after(150, self._carregar_dados)

    def _montar_interface(self) -> None:
        self._label_titulo = ctk.CTkLabel(
            self,
            text="Carregando titulo...",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
        )
        self._label_titulo.pack(fill="x", padx=20, pady=(16, 4))

        self._label_subtitulo = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
            anchor="w",
        )
        self._label_subtitulo.pack(fill="x", padx=20, pady=(0, 12))

        self._seletor_aba = ctk.CTkSegmentedButton(
            self,
            values=list(NOMES_ABAS),
            command=self._trocar_aba,
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            selected_hover_color=CORES["primariaHover"],
            unselected_color=CORES["superficie"],
            unselected_hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        )
        self._seletor_aba.pack(fill="x", padx=16, pady=(0, 8))
        self._seletor_aba.set(NOMES_ABAS[0])

        self._container_abas = ctk.CTkFrame(self, fg_color="transparent")
        self._container_abas.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        for nome in NOMES_ABAS:
            frame = ctk.CTkScrollableFrame(
                self._container_abas,
                fg_color=CORES["fundo"],
            )
            self._frames_por_aba[nome] = frame

        self._trocar_aba(NOMES_ABAS[0])

    def _trocar_aba(self, nome: str) -> None:
        if self._container_abas is None:
            return
        for frame in self._frames_por_aba.values():
            frame.pack_forget()
        self._frames_por_aba[nome].pack(fill="both", expand=True)

    def _carregar_dados(self) -> None:
        def tarefa():
            return self._controlador.obter_detalhes(self._identificador)

        def ao_concluir(resultado, erro_thread):
            if erro_thread:
                messagebox.showerror("Tesouro Direto", erro_thread, parent=self)
                self.destroy()
                return
            if resultado is None:
                messagebox.showerror("Tesouro Direto", "Resposta vazia do servidor.", parent=self)
                self.destroy()
                return

            detalhes, erro = resultado
            if erro:
                messagebox.showerror("Tesouro Direto", erro, parent=self)
                self.destroy()
                return
            if detalhes is None:
                messagebox.showerror("Tesouro Direto", "Titulo nao encontrado.", parent=self)
                self.destroy()
                return

            self._detalhes = detalhes
            titulo = detalhes.titulo
            self.title(f"Tesouro — {titulo.familia} ({titulo.data_vencimento_texto})")
            self._label_titulo.configure(text=titulo.tipo_titulo)
            self._label_subtitulo.configure(
                text=(
                    f"Familia: {titulo.familia}  |  Vencimento: {titulo.data_vencimento_texto}  |  "
                    f"Cotacao: {titulo.data_base_texto}"
                )
            )
            info_familia = self._controlador.obter_informacoes_familia(titulo.familia)
            self._montar_aba_cotacao(detalhes)
            self._montar_aba_simular(detalhes)
            self._montar_aba_caracteristicas(info_familia)
            self._montar_aba_impostos(info_familia)
            self._montar_aba_historico(detalhes)

        executar_em_thread(self, tarefa, ao_concluir)

    def _limpar_frame(self, nome_aba: str) -> None:
        frame = self._frames_por_aba[nome_aba]
        for widget in frame.winfo_children():
            widget.destroy()

    def _montar_aba_cotacao(self, detalhes: DetalhesTituloTesouro) -> None:
        self._limpar_frame("Cotacao")
        scroll = self._frames_por_aba["Cotacao"]
        titulo = detalhes.titulo

        self._adicionar_secao(scroll, "Precos e taxas (manha)")
        linhas = [
            ("Taxa de venda", self._formatar_taxa(titulo.taxa_venda)),
            ("Taxa de compra", self._formatar_taxa(titulo.taxa_compra)),
            ("PU venda", formatar_moeda(titulo.pu_venda) if titulo.pu_venda else "—"),
            ("PU compra", formatar_moeda(titulo.pu_compra) if titulo.pu_compra else "—"),
            ("PU base", formatar_moeda(titulo.pu_base) if titulo.pu_base else "—"),
            ("Data base", titulo.data_base_texto),
            ("Data vencimento", titulo.data_vencimento_texto),
        ]
        for rotulo, valor in linhas:
            self._adicionar_linha_info(scroll, rotulo, valor)

        if detalhes.volatilidade_indicativa_pct is not None:
            self._adicionar_secao(scroll, "Volatilidade indicativa (ultimos 90 dias)")
            self._adicionar_linha_info(
                scroll,
                "Desvio do PU base",
                f"{detalhes.volatilidade_indicativa_pct:.2f}% em relacao a media",
            )
            if detalhes.amplitude_pu_pct is not None:
                self._adicionar_linha_info(
                    scroll,
                    "Amplitude min/max",
                    f"{detalhes.amplitude_pu_pct:.2f}% entre minimo e maximo",
                )
            self._adicionar_texto(
                scroll,
                "Calculado sobre o PU base diario publicado no CSV oficial. "
                "Serve como referencia de oscilacao de preco antes do vencimento; "
                "nao e volatilidade anualizada de mercado.",
            )

        ctk.CTkButton(
            scroll,
            text=self._controlador.obter_rotulo_botao_site(
                titulo.familia,
                titulo.data_vencimento_texto,
            ),
            command=lambda: webbrowser.open(
                self._controlador.obter_url_site(
                    titulo.tipo_titulo,
                    titulo.data_vencimento_texto,
                )
            ),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(anchor="w", padx=4, pady=(12, 8))

    def _montar_aba_simular(self, detalhes: DetalhesTituloTesouro) -> None:
        self._limpar_frame("Simular")
        scroll = self._frames_por_aba["Simular"]
        titulo = detalhes.titulo

        self._adicionar_secao(scroll, "Simular investimento ate o vencimento")
        self._adicionar_texto(
            scroll,
            f"Periodo: hoje ate {titulo.data_vencimento_texto} "
            f"(taxa de referencia: {self._formatar_taxa(titulo.taxa_venda)}). "
            "Compare o Tesouro com 100% CDI no mesmo intervalo, ja descontando IR estimado.",
        )

        linha_entrada = ctk.CTkFrame(scroll, fg_color="transparent")
        linha_entrada.pack(fill="x", padx=4, pady=(4, 8))

        ctk.CTkLabel(
            linha_entrada,
            text="Valor a aplicar",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left", padx=(0, 8))

        self._entrada_valor_simulacao = ctk.CTkEntry(
            linha_entrada,
            width=200,
            placeholder_text="R$ 10.000,00",
        )
        self._entrada_valor_simulacao.pack(side="left", padx=(0, 8))
        aplicar_mascara_moeda_ptbr(self._entrada_valor_simulacao)
        self._entrada_valor_simulacao.bind("<Return>", lambda _e: self._executar_simulacao())

        ctk.CTkButton(
            linha_entrada,
            text="Simular",
            command=self._executar_simulacao,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=120,
        ).pack(side="left")

        self._frame_resultado_simulacao = ctk.CTkFrame(scroll, fg_color="transparent")
        self._frame_resultado_simulacao.pack(fill="x", padx=4, pady=(8, 4))

        ctk.CTkLabel(
            scroll,
            text="Informe o valor e clique em Simular para ver rendimento, impostos e comparacao com CDI.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=820,
            justify="left",
        ).pack(anchor="w", padx=4, pady=(0, 8))

    def _executar_simulacao(self) -> None:
        if self._detalhes is None or self._entrada_valor_simulacao is None:
            return
        if self._frame_resultado_simulacao is None:
            return

        valor_texto = self._entrada_valor_simulacao.get()
        identificador = self._identificador

        for widget in self._frame_resultado_simulacao.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self._frame_resultado_simulacao,
            text="Calculando Tesouro e CDI (Banco Central)...",
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", pady=8)

        def tarefa():
            return self._controlador.simular_investimento(identificador, valor_texto)

        def ao_concluir(resultado, erro_thread):
            for widget in self._frame_resultado_simulacao.winfo_children():
                widget.destroy()

            if erro_thread:
                messagebox.showerror("Simulacao", erro_thread, parent=self)
                return

            simulacao, erro = resultado
            if erro:
                messagebox.showerror("Simulacao", erro, parent=self)
                return
            if simulacao is None:
                messagebox.showerror("Simulacao", "Nao foi possivel simular.", parent=self)
                return

            self._preencher_resultado_simulacao(simulacao)

        executar_em_thread(self, tarefa, ao_concluir)

    def _preencher_resultado_simulacao(self, sim: ResultadoSimulacaoTesouro) -> None:
        if self._frame_resultado_simulacao is None:
            return

        self._adicionar_bloco_destaque(
            self._frame_resultado_simulacao,
            "Periodo",
            (
                f"De {sim.data_inicio_texto} ate {sim.data_fim_texto} "
                f"({sim.dias_periodo} dias). Taxa: {sim.taxa_tesouro_rotulo}."
            ),
        )

        for obs in sim.observacoes:
            self._adicionar_texto(self._frame_resultado_simulacao, f"• {obs}")

        self._adicionar_secao(self._frame_resultado_simulacao, "Tesouro Direto (estimativa no vencimento)")

        linhas_tesouro = [
            ("Valor aplicado", formatar_moeda(sim.valor_inicial)),
            ("Valor bruto no vencimento", formatar_moeda(sim.valor_bruto_tesouro)),
            ("Rendimento bruto", formatar_moeda(sim.rendimento_bruto_tesouro)),
            ("Taxa de custodia (estimada)", formatar_moeda(sim.taxa_custodia_estimada)),
            ("IOF", formatar_moeda(sim.iof_tesouro)),
            (
                f"Imposto de Renda ({sim.aliquota_ir_tesouro:.2f}%)",
                formatar_moeda(sim.imposto_ir_tesouro),
            ),
            ("Valor liquido", formatar_moeda(sim.valor_liquido_tesouro)),
            (
                "Ganho liquido",
                f"{formatar_moeda(sim.rendimento_liquido_tesouro)} ({sim.rendimento_liquido_tesouro_pct:.2f}%)",
            ),
        ]
        for rotulo, valor in linhas_tesouro:
            self._adicionar_linha_info(self._frame_resultado_simulacao, rotulo, valor)

        if sim.valor_liquido_cdi is not None:
            self._adicionar_secao(self._frame_resultado_simulacao, "100% CDI (mesmo periodo)")

            linhas_cdi = [
                ("Valor aplicado", formatar_moeda(sim.valor_inicial)),
                ("Valor bruto", formatar_moeda(sim.valor_bruto_cdi or 0)),
                ("Rendimento bruto", formatar_moeda(sim.rendimento_bruto_cdi or 0)),
                (
                    f"Imposto de Renda ({sim.aliquota_ir_cdi:.2f}%)"
                    if sim.aliquota_ir_cdi is not None
                    else "Imposto de Renda",
                    formatar_moeda(sim.imposto_ir_cdi or 0),
                ),
                ("Valor liquido", formatar_moeda(sim.valor_liquido_cdi)),
                (
                    "Ganho liquido",
                    f"{formatar_moeda(sim.rendimento_liquido_cdi or 0)} "
                    f"({sim.rendimento_liquido_cdi_pct:.2f}%)",
                ),
            ]
            for rotulo, valor in linhas_cdi:
                self._adicionar_linha_info(self._frame_resultado_simulacao, rotulo, valor)

            self._adicionar_secao(self._frame_resultado_simulacao, "Comparacao")

            if sim.diferenca_liquida_vs_cdi is not None:
                sinal = "+" if sim.diferenca_liquida_vs_cdi >= 0 else ""
                vencedor = (
                    "Tesouro liquido maior que CDI"
                    if sim.diferenca_liquida_vs_cdi >= 0
                    else "CDI liquido maior que Tesouro"
                )
                self._adicionar_bloco_destaque(
                    self._frame_resultado_simulacao,
                    vencedor,
                    (
                        f"Diferenca no ganho liquido: {sinal}{formatar_moeda(sim.diferenca_liquida_vs_cdi)} "
                        f"a favor do Tesouro (negativo favorece o CDI)."
                    ),
                )

        card_aviso = ctk.CTkFrame(
            self._frame_resultado_simulacao,
            fg_color=CORES.get("destaqueAvisoLegal", CORES["avisoFundo"]),
            corner_radius=8,
        )
        card_aviso.pack(fill="x", pady=(12, 4))
        ctk.CTkLabel(
            card_aviso,
            text=sim.aviso,
            font=ctk.CTkFont(size=11),
            text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
            wraplength=800,
            justify="left",
        ).pack(anchor="w", padx=12, pady=10)

    def _montar_aba_caracteristicas(
        self,
        info: InformacoesFamiliaTesouro | None,
    ) -> None:
        self._limpar_frame("Caracteristicas")
        scroll = self._frames_por_aba["Caracteristicas"]

        if info is None:
            self._adicionar_texto(scroll, "Informacoes da familia nao disponiveis para este titulo.")
            return

        self._adicionar_secao(scroll, info.nome)
        self._adicionar_texto(scroll, info.resumo)

        campos = [
            ("Rentabilidade", info.rentabilidade),
            ("Volatilidade", info.volatilidade),
            ("Liquidez", info.liquidez),
            ("Risco", info.risco),
            ("Perfil do investidor", info.perfil_investidor),
            ("Pagamento de juros", info.pagamento_juros),
            ("Investimento minimo", info.investimento_minimo),
            ("Quando faz sentido", info.quando_faz_sentido),
        ]
        for rotulo, texto in campos:
            self._adicionar_bloco_destaque(scroll, rotulo, texto)

        self._adicionar_secao(scroll, "Indicadores gerais do Tesouro Direto")
        for indicador in self._controlador.obter_indicadores_gerais():
            self._adicionar_bloco_destaque(scroll, indicador.rotulo, indicador.explicacao, indicador.valor)

    def _montar_aba_impostos(self, info: InformacoesFamiliaTesouro | None) -> None:
        self._limpar_frame("Impostos")
        scroll = self._frames_por_aba["Impostos"]

        tributacao = info.tributacao if info else "Consulte as regras vigentes no site oficial."
        self._adicionar_secao(scroll, "Tributacao desta familia")
        self._adicionar_texto(scroll, tributacao)

        self._adicionar_secao(scroll, "Imposto de Renda (regressivo)")
        self._adicionar_texto(
            scroll,
            "Sobre o rendimento na venda ou no vencimento:\n"
            "• Ate 180 dias: 22,5%\n"
            "• De 181 a 360 dias: 20%\n"
            "• De 361 a 720 dias: 17,5%\n"
            "• Acima de 720 dias: 15%",
        )

        self._adicionar_secao(scroll, "IOF")
        self._adicionar_texto(
            scroll,
            "Se resgatar antes de 30 dias da aplicacao, incide IOF regressivo sobre o rendimento, "
            "além do Imposto de Renda.",
        )

        self._adicionar_secao(scroll, "Custos")
        self._adicionar_texto(
            scroll,
            "Taxa de custodia do Tesouro Direto: ate 0,20% ao ano sobre o saldo, cobrada semestralmente. "
            "Muitas corretoras isentam essa taxa. Verifique também a taxa de operacao da sua corretora.",
        )

    def _montar_aba_historico(self, detalhes: DetalhesTituloTesouro) -> None:
        self._limpar_frame("Historico PU")
        scroll = self._frames_por_aba["Historico PU"]

        historico = detalhes.historico_pu
        if not historico:
            self._adicionar_texto(scroll, "Historico de PU indisponivel para este titulo.")
            return

        self._adicionar_secao(scroll, f"PU base — ultimos {len(historico)} dias uteis (amostra)")
        adicionar_cabecalho_tabela(scroll, ["Data base", "PU base (R$)"])

        for indice, ponto in enumerate(reversed(historico[-60:])):
            pu_texto = formatar_moeda(ponto.pu_base) if ponto.pu_base else "—"
            adicionar_linha_zebrada(scroll, [ponto.data_base_texto, pu_texto], indice)

    def _adicionar_secao(self, pai: ctk.CTkFrame, titulo: str) -> None:
        ctk.CTkLabel(
            pai,
            text=titulo,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
        ).pack(anchor="w", padx=4, pady=(12, 4))

    def _adicionar_texto(self, pai: ctk.CTkFrame, texto: str) -> None:
        ctk.CTkLabel(
            pai,
            text=texto,
            font=ctk.CTkFont(size=14),
            text_color=CORES["texto"],
            wraplength=820,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=4, pady=(0, 8))

    def _adicionar_linha_info(self, pai: ctk.CTkFrame, rotulo: str, valor: str) -> None:
        linha = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=8)
        linha.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(
            linha,
            text=rotulo,
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
            width=180,
            anchor="w",
        ).pack(side="left", padx=12, pady=8)
        ctk.CTkLabel(
            linha,
            text=formatar_texto_opcional(valor),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
        ).pack(side="left", padx=8, pady=8)

    def _adicionar_bloco_destaque(
        self,
        pai: ctk.CTkFrame,
        rotulo: str,
        texto: str,
        valor_destaque: str | None = None,
    ) -> None:
        card = ctk.CTkFrame(
            pai,
            fg_color=CORES["superficie"],
            corner_radius=8,
            border_width=1,
            border_color=CORES["borda"],
        )
        card.pack(fill="x", padx=4, pady=4)

        cab = rotulo
        if valor_destaque:
            cab = f"{rotulo}: {valor_destaque}"
        ctk.CTkLabel(
            card,
            text=cab,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["primaria"],
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            card,
            text=texto,
            font=ctk.CTkFont(size=13),
            text_color=CORES["texto"],
            wraplength=800,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 10))

    @staticmethod
    def _formatar_taxa(valor: float | None) -> str:
        if valor is None:
            return "—"
        return f"{valor:.2f}%".replace(".", ",")
