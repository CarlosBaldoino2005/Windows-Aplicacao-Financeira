"""Hub de ETFs com painel em alta / queda / todas filtrado por periodo."""
from __future__ import annotations

from datetime import datetime
from tkinter import ttk

from src.View import mensagem_helper as messagebox

import customtkinter as ctk

from src.Controller.controlador_etfs import ControladorEtfs
from src.Model.cotacao import CotacaoResumo
from src.Model.periodos_mercado import PERIODOS_MERCADO, periodo_chave_por_rotulo
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.atualizacao_automatica_helper import GerenciadorAtualizacaoAutomatica
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.View.hub_painel_config_helper import ConfiguracaoHubPainel
from src.View.janela_comparar_acoes import JanelaCompararAcoes
from src.View.janela_favoritas import JanelaFavoritas
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.janela_noticias_mercado import JanelaNoticiasMercado
from src.View.janela_pesquisa_acao import JanelaPesquisaAcao
from src.View.tabela_mercado_helper import (
    criar_card_tabela,
    definir_rotulo_coluna_variacao,
    obter_simbolo_duplo_clique_treeview,
    preencher_tabela as preencher_tabela_mercado,
    reaplicar_fonte_em_tabelas,
)
from src.View.tema import CORES


class JanelaHubEtfsPainelPeriodo(ctk.CTkToplevel):
    """Mesma estrutura de Acoes por periodo, para ETFs."""

    def __init__(self, pai: ctk.CTk) -> None:
        super().__init__(pai)
        self._controlador = ControladorEtfs()
        self._config_painel = ConfigPainelIni()
        self._periodo_rotulo_atual = "Mes"
        self._janela_pesquisa: JanelaPesquisaAcao | None = None
        self._janela_favoritas: JanelaFavoritas | None = None
        self._janela_comparar: JanelaCompararAcoes | None = None
        self._janela_noticias: JanelaNoticiasMercado | None = None
        self._janela_grafico: JanelaGraficoAcao | None = None
        self._carga_inicial_feita = False
        self._painel_buscando = False
        self._atualizador_auto = None
        self._config_hub = ConfiguracaoHubPainel(
            self,
            self._config_painel,
            escopo_quantidade="etfs",
            ao_recarregar=lambda: self._carregar_painel(),
            ao_mudar_fonte=self._ao_mudar_fonte_grid,
            ao_remontar_layout=self._reconstruir_interface_apos_tema,
            ao_reagendar_auto=self._reagendar_atualizacao_automatica,
        )

        self.title("ETFs por periodo")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 600)

        self._montar_layout()
        configurar_janela_maximizada(self, janela_pai=pai)
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

        self._config_hub.montar_titulo_com_engrenagem(cabecalho, "ETFs por periodo")

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Em alta, em queda e todos os ETFs monitorados com variacao "
                "no periodo selecionado (dia, semana, mes, trimestre, semestre, ano, "
                "3 anos, 5 anos ou personalizado)."
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
            text="Consultas e periodo",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        linha_botoes = ctk.CTkFrame(card, fg_color="transparent")
        linha_botoes.pack(anchor="w", padx=12, pady=(0, 8))

        for texto, comando in (
            ("Pesquisar ETF", self._abrir_pesquisa),
            ("Favoritos", self._abrir_favoritas),
            ("Comparar", self._abrir_comparar),
            ("Noticias", self._abrir_noticias),
        ):
            ctk.CTkButton(
                linha_botoes,
                text=texto,
                command=comando,
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=170,
                height=36,
            ).pack(side="left", padx=(0, 8))

        linha_periodo = ctk.CTkFrame(card, fg_color="transparent")
        linha_periodo.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(linha_periodo, text="Periodo").pack(side="left", padx=(0, 8))
        self._combo_periodo = ctk.CTkComboBox(
            linha_periodo,
            values=[p[1] for p in PERIODOS_MERCADO],
            width=140,
            command=self._alternar_datas,
        )
        self._combo_periodo.set("Mes")
        self._combo_periodo.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            linha_periodo,
            text="Atualizar painel",
            command=self._carregar_painel,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=140,
        ).pack(side="left", padx=(0, 12))

        self._frame_datas = ctk.CTkFrame(linha_periodo, fg_color="transparent")
        ctk.CTkLabel(self._frame_datas, text="Inicio (dd/mm/aaaa)").pack(side="left", padx=(0, 6))
        self._entrada_inicio = ctk.CTkEntry(self._frame_datas, width=110)
        self._entrada_inicio.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(self._frame_datas, text="Fim (dd/mm/aaaa)").pack(side="left", padx=(0, 6))
        self._entrada_fim = ctk.CTkEntry(self._frame_datas, width=110)
        self._entrada_fim.pack(side="left")

        barra = ctk.CTkFrame(card, fg_color="transparent")
        barra.pack(fill="x", padx=12, pady=(0, 12))

        qtd = self._config_painel.carregar()
        self._label_status = ctk.CTkLabel(
            barra,
            text=f"Carregando ate {qtd} ETFs no periodo Mes...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(side="left")

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

    def _periodo_chave(self) -> str:
        return periodo_chave_por_rotulo(self._combo_periodo.get())

    def _alternar_datas(self, _valor=None) -> None:
        if self._periodo_chave() == "personalizado":
            self._frame_datas.pack(side="left", padx=(12, 0))
        else:
            self._frame_datas.pack_forget()

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
            self._titulo_aba("alta"),
        )
        self._tabela_queda = self._criar_tabela_aba(
            self._aba_queda,
            self._titulo_aba("queda"),
        )
        self._tabela_todas = self._criar_tabela_aba(
            self._aba_todas,
            self._titulo_aba("todas"),
        )
        self._trocar_aba("Em alta")

    def _titulo_aba(self, tipo: str) -> str:
        periodo = self._periodo_rotulo_atual
        textos = {
            "alta": f"ETFs em alta no periodo: {periodo}",
            "queda": f"ETFs em queda no periodo: {periodo}",
            "todas": f"Todos os ETFs no periodo: {periodo}",
        }
        return textos.get(tipo, f"ETFs — {periodo}") + " (duplo clique abre o grafico)"

    def _atualizar_titulos_abas(self) -> None:
        for tabela, tipo in (
            (self._tabela_alta, "alta"),
            (self._tabela_queda, "queda"),
            (self._tabela_todas, "todas"),
        ):
            label = getattr(tabela, "_label_titulo_card", None)
            if label is not None:
                label.configure(text=self._titulo_aba(tipo))

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
        self._janela_pesquisa.title("Pesquisar ETF")

    def _abrir_favoritas(self) -> None:
        if self._focar_janela(self._janela_favoritas):
            self._janela_favoritas._atualizar_grid()
            return
        self._janela_favoritas = JanelaFavoritas(
            self, self._controlador, tipo_painel="etfs"
        )
        self._janela_favoritas.title("Favoritos — ETFs")

    def _abrir_comparar(self) -> None:
        if self._focar_janela(self._janela_comparar):
            return
        self._janela_comparar = JanelaCompararAcoes(
            self, self._controlador, modo_somente_etfs=True
        )
        self._janela_comparar.title("Comparar ETFs")

    def _abrir_noticias(self) -> None:
        if self._focar_janela(self._janela_noticias):
            return
        self._janela_noticias = JanelaNoticiasMercado(self, self._controlador)
        self._janela_noticias.title("Noticias — ETFs")

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
        periodo = self._periodo_chave()
        data_ini = self._entrada_inicio.get().strip() if periodo == "personalizado" else None
        data_fim = self._entrada_fim.get().strip() if periodo == "personalizado" else None
        self._janela_grafico = JanelaGraficoAcao(
            self,
            self._controlador,
            simbolo,
            periodo_chave=periodo,
            data_inicio=data_ini,
            data_fim=data_fim,
        )
        codigo = simbolo.replace(".SA", "")
        rotulo = self._combo_periodo.get()
        self._janela_grafico.title(f"Grafico — {codigo} ({rotulo})")

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _carregar_painel(self, automatico: bool = False) -> None:
        if automatico and self._painel_buscando:
            return

        quantidade = self._config_painel.carregar()

        periodo = self._periodo_chave()
        rotulo_periodo = self._combo_periodo.get()
        self._periodo_rotulo_atual = rotulo_periodo
        self._atualizar_titulos_abas()

        self._painel_buscando = True
        self._label_status.configure(
            text=f"Calculando variacao no periodo {rotulo_periodo} para ate {quantidade} ETFs..."
        )

        data_ini = self._entrada_inicio.get().strip() if periodo == "personalizado" else None
        data_fim = self._entrada_fim.get().strip() if periodo == "personalizado" else None

        def buscar():
            return self._controlador.obter_painel_periodo(
                quantidade,
                periodo,
                data_ini,
                data_fim,
            )

        def ao_concluir(resultado, erro_thread):
            self._painel_buscando = False
            if erro_thread:
                self._label_status.configure(text=erro_thread, text_color=CORES["erro"])
                if not automatico:
                    messagebox.showerror("Erro", erro_thread, parent=self)
                return

            dados, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                if not automatico:
                    messagebox.showwarning("ETFs por periodo", msg_erro, parent=self)
                return

            rotulo_var = f"Var. no periodo ({dados['periodo_rotulo']})"
            for tabela in (self._tabela_alta, self._tabela_queda, self._tabela_todas):
                definir_rotulo_coluna_variacao(tabela, rotulo_var)

            self._preencher(
                self._tabela_alta,
                dados["em_alta"],
                f"Nenhum ETF em alta no periodo {dados['periodo_rotulo']}.",
            )
            self._preencher(
                self._tabela_queda,
                dados["em_queda"],
                f"Nenhum ETF em queda no periodo {dados['periodo_rotulo']}.",
            )
            self._preencher(self._tabela_todas, dados["todas"])
            self._trocar_aba("Em alta")
            self._seletor_abas.set("Em alta")

            hora = datetime.now().strftime("%H:%M:%S")
            self._label_status.configure(
                text=(
                    f"Atualizado as {hora} — periodo {dados['periodo_rotulo']} | "
                    f"com dados {dados['total_com_dados']} | "
                    f"alta {len(dados['em_alta'])} | "
                    f"baixa {len(dados['em_queda'])} | "
                    f"todas {len(dados['todas'])}"
                ),
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
