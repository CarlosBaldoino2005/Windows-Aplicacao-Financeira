"""Hub de LCI/LCA ou CDB com informacoes, indicadores BCB e simulacao."""
from __future__ import annotations

import webbrowser
from typing import Literal

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Controller.controlador_renda_fixa_bancaria import ControladorRendaFixaBancaria
from src.Model.oferta_renda_fixa_bancaria import OfertaRendaFixaBancaria
from src.Model.renda_fixa_bancaria_informacoes import InformacoesProdutoRendaFixa
from src.Model.simulacao_renda_fixa_bancaria import ResultadoSimulacaoRendaFixaBancaria
from src.Service.indicadores_mercado_servico import IndicadoresMercado
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr
from src.Tool.simulacao_valor_ini_helper import (
    configurar_entrada_valor_simulacao,
    persistir_valor_simulacao_da_entrada,
)
from src.Tool.formatar_prazo_helper import montar_prazo_legivel, montar_texto_celula_prazo
from src.View.formatadores import formatar_moeda, formatar_texto_opcional
from src.View.hub_painel_config_helper import ConfiguracaoHubPainel
from src.View.prazo_legivel_helper import adicionar_linha_prazo_legivel
from src.View.grid_ordenacao_helper import EstadoOrdenacaoColuna, LinhaTabelaOrdenavel
from src.View.tabela_detalhes_helper import renderizar_tabela_zebrada
from src.View.tema import CORES

ModoHub = Literal["lci_lca", "cdb"]
URL_FGC = "https://www.fgc.org.br/"
URL_BCB = "https://www.bcb.gov.br/"
URL_MEELION_COMPARADOR = "https://www.meelion.com/renda-fixa/comparar-investimentos/"

_COLUNAS_OFERTAS = ["Tipo", "Emissor", "Taxa", "Vencimento", "Minimo", "Liquida a.a."]


class JanelaHubRendaFixaBancaria(ctk.CTkToplevel):
    """Painel educativo e simulador para renda fixa bancaria."""

    def __init__(self, pai: ctk.CTk, modo: ModoHub) -> None:
        super().__init__(pai)
        self._modo = modo
        self._controlador = ControladorRendaFixaBancaria()
        self._config_painel = ConfigPainelIni()
        self._frames_por_aba: dict[str, ctk.CTkScrollableFrame] = {}
        self._frame_resultado_sim: ctk.CTkFrame | None = None
        self._entrada_valor: ctk.CTkEntry | None = None
        self._entrada_prazo: ctk.CTkEntry | None = None
        self._entrada_pct_cdi: ctk.CTkEntry | None = None
        self._entrada_taxa_prefix: ctk.CTkEntry | None = None
        self._combo_produto: ctk.CTkComboBox | None = None
        self._seletor_modalidade: ctk.CTkSegmentedButton | None = None
        self._frame_campos_cdi: ctk.CTkFrame | None = None
        self._frame_campos_prefix: ctk.CTkFrame | None = None
        self._label_indicadores_status: ctk.CTkLabel | None = None
        self._ofertas: list[OfertaRendaFixaBancaria] = []
        self._scroll_ofertas: ctk.CTkScrollableFrame | None = None
        self._ordenacao_ofertas = EstadoOrdenacaoColuna()
        self._label_status_ofertas: ctk.CTkLabel | None = None
        self._combo_distribuidor: ctk.CTkComboBox | None = None
        self._combo_prazo: ctk.CTkComboBox | None = None
        self._check_apenas_emissor: ctk.CTkCheckBox | None = None
        self._url_comparador_ofertas: str = URL_MEELION_COMPARADOR
        self._mapa_prazo_slug: dict[str, str] = {}
        self._config_hub = ConfiguracaoHubPainel(
            self,
            self._config_painel,
            incluir_quantidade=False,
            ao_remontar_layout=self._reconstruir_interface_apos_tema,
        )

        titulo = "LCI / LCA" if modo == "lci_lca" else "CDB"
        self.title(titulo)
        self.configure(fg_color=CORES["fundo"])
        self.minsize(920, 640)

        self._nomes_abas = self._montar_lista_abas()
        self._montar_layout()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()
        self.after(150, self._carregar_indicadores)

    def _montar_lista_abas(self) -> list[str]:
        if self._modo == "lci_lca":
            return ["LCI", "LCA", "Ofertas", "Simular", "Indicadores"]
        return ["Sobre CDB", "Ofertas", "Simular", "Indicadores"]

    def _montar_layout(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        titulo = "LCI / LCA" if self._modo == "lci_lca" else "CDB"
        subtitulo = (
            "Letras de credito isentas de IR para pessoa fisica. "
            "Compare ofertas do seu banco com 100% CDI na simulacao."
            if self._modo == "lci_lca"
            else "Certificado de deposito bancario. Simule taxa liquida versus 100% CDI."
        )

        self._config_hub.montar_titulo_com_engrenagem(cabecalho, titulo)

        ctk.CTkLabel(
            cabecalho,
            text=subtitulo,
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self._seletor_aba = ctk.CTkSegmentedButton(
            self,
            values=self._nomes_abas,
            command=self._trocar_aba,
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            selected_hover_color=CORES["primariaHover"],
            unselected_color=CORES["superficie"],
            unselected_hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        )
        self._seletor_aba.pack(fill="x", padx=16, pady=(0, 8))
        self._seletor_aba.set(self._nomes_abas[0])

        self._container_abas = ctk.CTkFrame(self, fg_color="transparent")
        self._container_abas.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        for nome in self._nomes_abas:
            if nome == "Ofertas":
                frame = ctk.CTkFrame(self._container_abas, fg_color=CORES["fundo"])
            else:
                frame = ctk.CTkScrollableFrame(self._container_abas, fg_color=CORES["fundo"])
            self._frames_por_aba[nome] = frame

        if self._modo == "lci_lca":
            self._montar_aba_produto("LCI", self._controlador.obter_informacoes_lci())
            self._montar_aba_produto("LCA", self._controlador.obter_informacoes_lca())
        else:
            self._montar_aba_produto("Sobre CDB", self._controlador.obter_informacoes_cdb())

        self._montar_aba_ofertas()
        self._montar_aba_simular()
        self._montar_aba_indicadores_placeholder()

        self._trocar_aba(self._nomes_abas[0])

        ctk.CTkLabel(
            self,
            text="Conteudo educativo. Ofertas reais dependem do banco — nao e recomendacao de investimento.",
            font=ctk.CTkFont(size=11),
            text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
            fg_color=CORES.get("destaqueAvisoLegal", CORES["avisoFundo"]),
            corner_radius=8,
        ).pack(fill="x", padx=16, pady=(0, 12))

    def _reconstruir_interface_apos_tema(self) -> None:
        aba_atual = self._seletor_aba.get() if self._seletor_aba is not None else self._nomes_abas[0]
        for widget in self.winfo_children():
            widget.destroy()
        self._frames_por_aba = {}
        self._frame_resultado_sim = None
        self._scroll_ofertas = None
        self._config_hub.limpar_referencia_modal()
        self.configure(fg_color=CORES["fundo"])
        self._montar_layout()
        if aba_atual in self._nomes_abas:
            self._seletor_aba.set(aba_atual)
            self._trocar_aba(aba_atual)
        self.after(150, self._carregar_indicadores)

    def _trocar_aba(self, nome: str) -> None:
        for frame in self._frames_por_aba.values():
            frame.pack_forget()
        self._frames_por_aba[nome].pack(fill="both", expand=True)
        if nome == "Ofertas" and not self._ofertas and self._combo_distribuidor is not None:
            self.after(100, self._buscar_ofertas)

    def _montar_aba_ofertas(self) -> None:
        pai = self._frames_por_aba["Ofertas"]

        ctk.CTkLabel(
            pai,
            text="Ofertas no mercado (Meelion)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            pai,
            text=(
                "Ranking parcial de LCI, LCA e CDB disponiveis no distribuidor escolhido "
                "(app/corretora). Duplo clique preenche a simulacao. Dados informativos — "
                "confirme no banco antes de investir."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=8, pady=(0, 8))

        barra = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=12)
        barra.pack(fill="x", padx=8, pady=(0, 8))

        linha_filtros = ctk.CTkFrame(barra, fg_color="transparent")
        linha_filtros.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            linha_filtros,
            text="Onde investir",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 8))
        distribuidores = self._controlador.obter_distribuidores_ofertas()
        self._combo_distribuidor = ctk.CTkComboBox(
            linha_filtros,
            values=distribuidores,
            width=220,
            state="readonly",
        )
        if distribuidores:
            self._combo_distribuidor.set(distribuidores[0])
        self._combo_distribuidor.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            linha_filtros,
            text="Prazo",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 8))
        opcoes_prazo = self._controlador.obter_opcoes_prazo_ofertas()
        rotulos_prazo = [rotulo for rotulo, _ in opcoes_prazo]
        self._mapa_prazo_slug = {rotulo: slug for rotulo, slug in opcoes_prazo}
        self._combo_prazo = ctk.CTkComboBox(
            linha_filtros,
            values=rotulos_prazo,
            width=160,
            state="readonly",
        )
        self._combo_prazo.set(rotulos_prazo[0] if rotulos_prazo else "Todos os prazos")
        self._combo_prazo.pack(side="left")

        linha_acoes = ctk.CTkFrame(barra, fg_color="transparent")
        linha_acoes.pack(fill="x", padx=12, pady=(4, 12))

        self._check_apenas_emissor = ctk.CTkCheckBox(
            linha_acoes,
            text="Somente titulos emitidos pelo banco selecionado",
            font=ctk.CTkFont(size=12),
        )
        self._check_apenas_emissor.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            linha_acoes,
            text="Buscar ofertas",
            command=self._buscar_ofertas,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=130,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            linha_acoes,
            text="Ver mais na Meelion",
            command=lambda: webbrowser.open(self._url_comparador_ofertas),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=160,
        ).pack(side="left")

        self._label_status_ofertas = ctk.CTkLabel(
            pai,
            text="Selecione o distribuidor e clique em Buscar ofertas.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status_ofertas.pack(anchor="w", padx=8, pady=(0, 4))

        card = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=12)
        card.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._scroll_ofertas = ctk.CTkScrollableFrame(card, fg_color=CORES["superficie"])
        self._scroll_ofertas.pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(
            pai,
            text="Fonte: Meelion. Exibe ate 5 melhores resultados por consulta (modo aberto da API).",
            font=ctk.CTkFont(size=11),
            text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
            fg_color=CORES.get("destaqueAvisoLegal", CORES["avisoFundo"]),
            corner_radius=8,
        ).pack(fill="x", padx=8, pady=(0, 8))

    def _buscar_ofertas(self) -> None:
        if self._combo_distribuidor is None:
            return

        distribuidor = self._combo_distribuidor.get().strip()
        prazo_slug = None
        if self._combo_prazo is not None:
            prazo_slug = self._mapa_prazo_slug.get(self._combo_prazo.get(), "")

        apenas_emissor = bool(
            self._check_apenas_emissor is not None and self._check_apenas_emissor.get()
        )

        if self._label_status_ofertas is not None:
            self._label_status_ofertas.configure(text=f"Buscando ofertas em {distribuidor}...")

        def tarefa():
            return self._controlador.buscar_ofertas(
                self._modo,
                distribuidor,
                prazo_slug,
                apenas_emissor,
            )

        def ao_concluir(resultado, erro_thread):
            if erro_thread:
                if self._label_status_ofertas is not None:
                    self._label_status_ofertas.configure(text=f"Erro: {erro_thread}")
                messagebox.showerror("Ofertas", erro_thread, parent=self)
                return

            consulta, erro = resultado
            if erro:
                if self._label_status_ofertas is not None:
                    self._label_status_ofertas.configure(text=erro)
                messagebox.showerror("Ofertas", erro, parent=self)
                return
            if consulta is None:
                return

            self._ofertas = consulta.ofertas
            if consulta.url_comparador:
                self._url_comparador_ofertas = consulta.url_comparador
            if self._label_status_ofertas is not None:
                texto_status = consulta.mensagem
                if consulta.atualizado_em:
                    texto_status += f" — atualizado em {consulta.atualizado_em[:19]}"
                self._label_status_ofertas.configure(text=texto_status)
            self._preencher_tabela_ofertas()

        executar_em_thread(self, tarefa, ao_concluir)

    def _preencher_tabela_ofertas(self) -> None:
        if self._scroll_ofertas is None:
            return

        for widget in self._scroll_ofertas.winfo_children():
            widget.destroy()

        if not self._ofertas:
            ctk.CTkLabel(
                self._scroll_ofertas,
                text="Nenhuma oferta encontrada com os filtros atuais.",
                font=ctk.CTkFont(size=13),
                text_color=CORES["textoSecundario"],
            ).pack(pady=24)
            return

        linhas: list[LinhaTabelaOrdenavel] = []
        for oferta in self._ofertas:
            prazo_venc = montar_prazo_legivel(
                dias=oferta.dias_ate_vencimento,
                data_fim=oferta.data_vencimento_texto,
            )
            linhas.append(
                LinhaTabelaOrdenavel(
                    valores=[
                        oferta.tipo,
                        oferta.emissor[:36] + ("…" if len(oferta.emissor) > 36 else ""),
                        oferta.taxa_rotulo,
                        montar_texto_celula_prazo(prazo_venc),
                        formatar_moeda(oferta.investimento_minimo)
                        if oferta.investimento_minimo is not None
                        else "—",
                        f"{oferta.taxa_liquida_aa:.2f}%".replace(".", ",")
                        if oferta.taxa_liquida_aa is not None
                        else "—",
                    ],
                    chaves=[
                        oferta.tipo,
                        oferta.emissor.lower(),
                        oferta.percentual_cdi
                        if oferta.percentual_cdi is not None
                        else oferta.taxa_prefixada_aa,
                        prazo_venc.dias_totais,
                        oferta.investimento_minimo if oferta.investimento_minimo is not None else -1.0,
                        oferta.taxa_liquida_aa if oferta.taxa_liquida_aa is not None else -1.0,
                    ],
                    ao_duplo_clique=lambda item=oferta: self._aplicar_oferta_na_simulacao(item),
                )
            )

        renderizar_tabela_zebrada(
            self._scroll_ofertas,
            _COLUNAS_OFERTAS,
            linhas,
            self._ordenacao_ofertas,
            self._preencher_tabela_ofertas,
            nome_arquivo_exportacao="renda_fixa_bancaria",
        )

    def _aplicar_oferta_na_simulacao(self, oferta: OfertaRendaFixaBancaria) -> None:
        if self._modo == "lci_lca" and self._combo_produto is not None:
            tipo = oferta.tipo.upper()
            if tipo in ("LCI", "LCA"):
                self._combo_produto.set(tipo)

        if oferta.dias_ate_vencimento is not None and self._entrada_prazo is not None:
            self._entrada_prazo.delete(0, "end")
            self._entrada_prazo.insert(0, str(max(1, oferta.dias_ate_vencimento)))

        if oferta.percentual_cdi is not None and self._seletor_modalidade is not None:
            self._seletor_modalidade.set("% CDI")
            self._ao_mudar_modalidade("% CDI")
            if self._entrada_pct_cdi is not None:
                self._entrada_pct_cdi.delete(0, "end")
                texto_pct = f"{oferta.percentual_cdi:.2f}".rstrip("0").rstrip(".").replace(".", ",")
                self._entrada_pct_cdi.insert(0, texto_pct)
        elif oferta.taxa_prefixada_aa is not None and self._seletor_modalidade is not None:
            self._seletor_modalidade.set("Prefixado")
            self._ao_mudar_modalidade("Prefixado")
            if self._entrada_taxa_prefix is not None:
                self._entrada_taxa_prefix.delete(0, "end")
                self._entrada_taxa_prefix.insert(
                    0,
                    f"{oferta.taxa_prefixada_aa:.2f}".replace(".", ","),
                )

        if self._seletor_aba is not None:
            self._seletor_aba.set("Simular")
            self._trocar_aba("Simular")

        messagebox.showinfo(
            "Simular",
            f"Dados de «{oferta.nome[:60]}» preenchidos na aba Simular.\n"
            "Ajuste o valor e clique em Simular e comparar com CDI.",
            parent=self,
        )

    def _montar_aba_produto(self, nome_aba: str, info: InformacoesProdutoRendaFixa) -> None:
        scroll = self._frames_por_aba[nome_aba]
        self._adicionar_secao(scroll, info.nome)
        self._adicionar_texto(scroll, info.resumo)

        campos = [
            ("Emissor", info.emissor),
            ("Rentabilidade", info.rentabilidade),
            ("Indexadores", info.indexadores),
            ("Liquidez", info.liquidez),
            ("Risco", info.risco),
            ("Tributacao", info.tributacao),
            ("FGC", info.fgc),
            ("Investimento minimo", info.investimento_minimo),
            ("Quando faz sentido", info.quando_faz_sentido),
            ("Cuidados", info.cuidados),
        ]
        for rotulo, texto in campos:
            self._adicionar_bloco(scroll, rotulo, texto)

        if nome_aba in ("LCI", "LCA", "Sobre CDB"):
            linha = ctk.CTkFrame(scroll, fg_color="transparent")
            linha.pack(fill="x", padx=4, pady=(8, 4))
            ctk.CTkButton(
                linha,
                text="Site FGC",
                command=lambda: webbrowser.open(URL_FGC),
                fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=100,
            ).pack(side="left", padx=(0, 8))

    def _montar_aba_simular(self) -> None:
        scroll = self._frames_por_aba["Simular"]
        self._adicionar_secao(scroll, "Simular investimento")
        self._adicionar_texto(
            scroll,
            "Informe valor, prazo e a taxa ofertada pelo banco. "
            "O sistema compara com 100% CDI (BCB) no mesmo periodo, ja descontando IR quando aplicavel.",
        )

        if self._modo == "lci_lca":
            linha_prod = ctk.CTkFrame(scroll, fg_color="transparent")
            linha_prod.pack(fill="x", padx=4, pady=4)
            ctk.CTkLabel(
                linha_prod,
                text="Produto",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=CORES["texto"],
            ).pack(side="left", padx=(0, 8))
            self._combo_produto = ctk.CTkComboBox(
                linha_prod,
                values=["LCI", "LCA"],
                width=120,
                state="readonly",
            )
            self._combo_produto.set("LCI")
            self._combo_produto.pack(side="left")

        linha_valor = ctk.CTkFrame(scroll, fg_color="transparent")
        linha_valor.pack(fill="x", padx=4, pady=4)
        ctk.CTkLabel(linha_valor, text="Valor", font=ctk.CTkFont(size=13, weight="bold")).pack(
            side="left", padx=(0, 8)
        )
        self._entrada_valor = ctk.CTkEntry(linha_valor, width=180, placeholder_text="R$ 10.000,00")
        self._entrada_valor.pack(side="left")
        aplicar_mascara_moeda_ptbr(self._entrada_valor)
        configurar_entrada_valor_simulacao(self._entrada_valor, self._config_painel)

        linha_prazo = ctk.CTkFrame(scroll, fg_color="transparent")
        linha_prazo.pack(fill="x", padx=4, pady=4)
        ctk.CTkLabel(linha_prazo, text="Prazo (dias)", font=ctk.CTkFont(size=13, weight="bold")).pack(
            side="left", padx=(0, 8)
        )
        self._entrada_prazo = ctk.CTkEntry(linha_prazo, width=100)
        self._entrada_prazo.insert(0, "365")
        self._entrada_prazo.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(
            linha_prazo,
            text="Ex.: 90, 180, 365, 720",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        ).pack(side="left")

        ctk.CTkLabel(
            scroll,
            text="Rentabilidade",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=4, pady=(12, 4))

        self._seletor_modalidade = ctk.CTkSegmentedButton(
            scroll,
            values=["% CDI", "Prefixado"],
            command=self._ao_mudar_modalidade,
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            selected_hover_color=CORES["primariaHover"],
            unselected_color=CORES["superficie"],
            unselected_hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        )
        self._seletor_modalidade.pack(anchor="w", padx=4, pady=(0, 8))
        self._seletor_modalidade.set("% CDI")

        self._frame_campos_cdi = ctk.CTkFrame(scroll, fg_color="transparent")
        self._frame_campos_cdi.pack(fill="x", padx=4, pady=4)
        ctk.CTkLabel(
            self._frame_campos_cdi,
            text="% do CDI",
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 8))
        self._entrada_pct_cdi = ctk.CTkEntry(self._frame_campos_cdi, width=80)
        self._entrada_pct_cdi.insert(0, "100")
        self._entrada_pct_cdi.pack(side="left")
        ctk.CTkLabel(
            self._frame_campos_cdi,
            text="(ex.: 95 = 95% CDI)",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        ).pack(side="left", padx=8)

        self._frame_campos_prefix = ctk.CTkFrame(scroll, fg_color="transparent")
        ctk.CTkLabel(
            self._frame_campos_prefix,
            text="Taxa a.a. (%)",
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 8))
        self._entrada_taxa_prefix = ctk.CTkEntry(self._frame_campos_prefix, width=80)
        self._entrada_taxa_prefix.insert(0, "12,5")
        self._entrada_taxa_prefix.pack(side="left")

        self._ao_mudar_modalidade("% CDI")

        ctk.CTkButton(
            scroll,
            text="Simular e comparar com CDI",
            command=self._executar_simulacao,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(anchor="w", padx=4, pady=(12, 8))

        self._frame_resultado_sim = ctk.CTkFrame(scroll, fg_color="transparent")
        self._frame_resultado_sim.pack(fill="x", padx=4, pady=4)

    def _ao_mudar_modalidade(self, valor: str) -> None:
        if self._frame_campos_cdi is None or self._frame_campos_prefix is None:
            return
        if valor == "% CDI":
            self._frame_campos_prefix.pack_forget()
            self._frame_campos_cdi.pack(fill="x", padx=4, pady=4)
        else:
            self._frame_campos_cdi.pack_forget()
            self._frame_campos_prefix.pack(fill="x", padx=4, pady=4)

    def _executar_simulacao(self) -> None:
        if self._frame_resultado_sim is None:
            return

        produto = "CDB"
        if self._modo == "lci_lca" and self._combo_produto is not None:
            produto = self._combo_produto.get().strip().upper()

        modalidade = "cdi" if self._seletor_modalidade and self._seletor_modalidade.get() == "% CDI" else "prefixado"
        valor_txt = self._entrada_valor.get() if self._entrada_valor else ""
        if self._entrada_valor is not None:
            persistir_valor_simulacao_da_entrada(self._entrada_valor, self._config_painel)
        prazo_txt = self._entrada_prazo.get() if self._entrada_prazo else ""
        pct_txt = self._entrada_pct_cdi.get() if self._entrada_pct_cdi else ""
        taxa_txt = self._entrada_taxa_prefix.get() if self._entrada_taxa_prefix else ""

        for widget in self._frame_resultado_sim.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self._frame_resultado_sim,
            text="Calculando...",
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", pady=8)

        def tarefa():
            return self._controlador.simular(
                produto,
                valor_txt,
                prazo_txt,
                modalidade,
                pct_txt,
                taxa_txt,
            )

        def ao_concluir(resultado, erro_thread):
            for widget in self._frame_resultado_sim.winfo_children():
                widget.destroy()
            if erro_thread:
                messagebox.showerror("Simulacao", erro_thread, parent=self)
                return
            sim, erro = resultado
            if erro:
                messagebox.showerror("Simulacao", erro, parent=self)
                return
            if sim:
                self._preencher_resultado_simulacao(sim)

        executar_em_thread(self, tarefa, ao_concluir)

    def _preencher_resultado_simulacao(self, sim: ResultadoSimulacaoRendaFixaBancaria) -> None:
        if self._frame_resultado_sim is None:
            return

        self._adicionar_secao(
            self._frame_resultado_sim,
            f"Resultado — {sim.produto} ({sim.taxa_rotulo})",
        )
        prazo = montar_prazo_legivel(
            dias=sim.dias_periodo,
            data_fim=sim.data_fim_texto,
            data_inicio=sim.data_inicio_texto,
        )
        adicionar_linha_prazo_legivel(self._frame_resultado_sim, "Periodo", prazo)
        for obs in sim.observacoes:
            self._adicionar_texto(self._frame_resultado_sim, f"• {obs}")

        linhas_prod = [
            ("Valor aplicado", formatar_moeda(sim.valor_inicial)),
            ("Valor bruto", formatar_moeda(sim.valor_bruto_produto)),
            ("Rendimento bruto", formatar_moeda(sim.rendimento_bruto_produto)),
            ("IOF", formatar_moeda(sim.iof_produto)),
            (
                f"IR ({sim.aliquota_ir_produto:.2f}%)",
                formatar_moeda(sim.imposto_ir_produto),
            ),
            ("Valor liquido", formatar_moeda(sim.valor_liquido_produto)),
            (
                "Ganho liquido",
                f"{formatar_moeda(sim.rendimento_liquido_produto)} ({sim.rendimento_liquido_produto_pct:.2f}%)",
            ),
        ]
        for rotulo, valor in linhas_prod:
            self._adicionar_linha(self._frame_resultado_sim, rotulo, valor)

        if sim.valor_liquido_cdi is not None:
            self._adicionar_secao(self._frame_resultado_sim, "100% CDI (referencia)")
            linhas_cdi = [
                ("Valor bruto", formatar_moeda(sim.valor_bruto_cdi or 0)),
                ("Rendimento bruto", formatar_moeda(sim.rendimento_bruto_cdi or 0)),
                (
                    f"IR ({sim.aliquota_ir_cdi:.2f}%)",
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
                self._adicionar_linha(self._frame_resultado_sim, rotulo, valor)

            if sim.diferenca_liquida_vs_cdi is not None:
                sinal = "+" if sim.diferenca_liquida_vs_cdi >= 0 else ""
                self._adicionar_bloco(
                    self._frame_resultado_sim,
                    "Comparacao",
                    f"Ganho liquido do {sim.produto} vs CDI: {sinal}{formatar_moeda(sim.diferenca_liquida_vs_cdi)}.",
                )

        self._adicionar_texto(self._frame_resultado_sim, sim.aviso)

    def _montar_aba_indicadores_placeholder(self) -> None:
        scroll = self._frames_por_aba["Indicadores"]
        self._label_indicadores_status = ctk.CTkLabel(
            scroll,
            text="Carregando indicadores do Banco Central...",
            text_color=CORES["textoSecundario"],
        )
        self._label_indicadores_status.pack(anchor="w", padx=4, pady=8)

    def _carregar_indicadores(self) -> None:
        def tarefa():
            return self._controlador.obter_indicadores_mercado(), self._controlador.obter_indicadores_gerais()

        def ao_concluir(resultado, erro_thread):
            scroll = self._frames_por_aba["Indicadores"]
            if self._label_indicadores_status is not None:
                self._label_indicadores_status.destroy()
                self._label_indicadores_status = None

            if erro_thread:
                self._adicionar_texto(scroll, f"Erro: {erro_thread}")
                return

            indicadores, gerais = resultado
            self._preencher_indicadores(scroll, indicadores, gerais)

        executar_em_thread(self, tarefa, ao_concluir)

    def _preencher_indicadores(self, scroll, ind: IndicadoresMercado, gerais) -> None:
        self._adicionar_secao(scroll, "Indicadores de mercado (BCB)")
        cdi_txt = f"{ind.cdi_aa_estimada:.2f}% a.a." if ind.cdi_aa_estimada is not None else "Indisponivel"
        selic_txt = f"{ind.selic_aa:.2f}% a.a." if ind.selic_aa is not None else "Indisponivel"
        self._adicionar_linha(scroll, "CDI estimado", cdi_txt)
        self._adicionar_linha(scroll, "Selic (serie diaria)", selic_txt)
        self._adicionar_linha(scroll, "Data referencia", ind.data_referencia_texto)
        self._adicionar_texto(scroll, ind.observacao)

        self._adicionar_secao(scroll, "Referencias uteis")
        for item in gerais:
            self._adicionar_bloco(scroll, f"{item.rotulo}: {item.valor}", item.explicacao)

        linha = ctk.CTkFrame(scroll, fg_color="transparent")
        linha.pack(fill="x", padx=4, pady=(8, 4))
        ctk.CTkButton(
            linha,
            text="Banco Central",
            command=lambda: webbrowser.open(URL_BCB),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            linha,
            text="FGC",
            command=lambda: webbrowser.open(URL_FGC),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(side="left")

    def _adicionar_secao(self, pai: ctk.CTkFrame, titulo: str) -> None:
        ctk.CTkLabel(
            pai,
            text=titulo,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=4, pady=(12, 4))

    def _adicionar_texto(self, pai: ctk.CTkFrame, texto: str) -> None:
        ctk.CTkLabel(
            pai,
            text=texto,
            font=ctk.CTkFont(size=13),
            text_color=CORES["texto"],
            wraplength=820,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=4, pady=(0, 6))

    def _adicionar_linha(self, pai: ctk.CTkFrame, rotulo: str, valor: str) -> None:
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

    def _adicionar_bloco(self, pai: ctk.CTkFrame, rotulo: str, texto: str) -> None:
        card = ctk.CTkFrame(
            pai,
            fg_color=CORES["superficie"],
            corner_radius=8,
            border_width=1,
            border_color=CORES["borda"],
        )
        card.pack(fill="x", padx=4, pady=4)
        ctk.CTkLabel(
            card,
            text=rotulo,
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
