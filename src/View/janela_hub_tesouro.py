"""Hub do Tesouro Direto — listagem de titulos publicos federais."""
from __future__ import annotations

import webbrowser

import customtkinter as ctk
from tkinter import messagebox

from src.Controller.controlador_tesouro import ControladorTesouro
from src.Model.titulo_tesouro import TituloTesouro
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread
from src.Tool.formatar_prazo_helper import montar_prazo_legivel, montar_texto_celula_prazo
from src.View.formatadores import formatar_moeda
from src.View.janela_detalhes_tesouro import JanelaDetalhesTesouro
from src.View.grid_ordenacao_helper import EstadoOrdenacaoColuna, LinhaTabelaOrdenavel
from src.View.tabela_detalhes_helper import renderizar_tabela_zebrada
from src.View.tema import CORES

URL_TESOURO_DIRETO = "https://www.tesourodireto.com.br/"
URL_TESOURO_TRANSPARENTE = "https://www.tesourotransparente.gov.br/"


class JanelaHubTesouro(ctk.CTkToplevel):
    """Painel com todos os titulos do Tesouro Direto e filtros por familia."""

    _COLUNAS = [
        "Familia",
        "Titulo",
        "Vencimento",
        "Taxa venda",
        "Taxa compra",
        "PU venda",
        "PU compra",
    ]

    def __init__(self, pai: ctk.CTk) -> None:
        super().__init__(pai)
        self._controlador = ControladorTesouro()
        self._titulos: list[TituloTesouro] = []
        self._familia_selecionada = "Todos"
        self._janela_detalhes: JanelaDetalhesTesouro | None = None
        self._scroll_tabela: ctk.CTkScrollableFrame | None = None
        self._ordenacao_tabela = EstadoOrdenacaoColuna()

        self.title("Tesouro Direto")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(960, 640)

        self._montar_layout()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(200, self._carregar_dados)

    def _ao_fechar(self) -> None:
        if self._janela_detalhes is not None:
            try:
                if self._janela_detalhes.winfo_exists():
                    self._janela_detalhes.destroy()
            except Exception:
                pass
        self.destroy()

    def _montar_layout(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Tesouro Direto",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=20, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Titulos publicos federais: Selic, Prefixado, IPCA+, IGPM+, Educa+ e Renda+. "
                "Duplo clique em uma linha para ver volatilidade, liquidez, tributacao e mais."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=920,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        barra = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        barra.pack(fill="x", padx=16, pady=(0, 8))

        self._label_status = ctk.CTkLabel(
            barra,
            text="Carregando cotacoes oficiais...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(side="left", padx=12, pady=12)

        ctk.CTkButton(
            barra,
            text="Site oficial",
            command=lambda: webbrowser.open(URL_TESOURO_DIRETO),
            fg_color=CORES["borda"],
            hover_color=CORES["zebraEscura"],
            width=100,
        ).pack(side="right", padx=(4, 12), pady=8)

        ctk.CTkButton(
            barra,
            text="Tesouro Transparente",
            command=lambda: webbrowser.open(URL_TESOURO_TRANSPARENTE),
            fg_color=CORES["borda"],
            hover_color=CORES["zebraEscura"],
            width=160,
        ).pack(side="right", padx=4, pady=8)

        ctk.CTkButton(
            barra,
            text="Atualizar",
            command=lambda: self._carregar_dados(forcar=True),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=100,
        ).pack(side="right", padx=4, pady=8)

        self._frame_filtro = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_filtro.pack(fill="x", padx=16, pady=(0, 8))

        card_tabela = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        card_tabela.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._scroll_tabela = ctk.CTkScrollableFrame(
            card_tabela,
            fg_color=CORES["superficie"],
        )
        self._scroll_tabela.pack(fill="both", expand=True, padx=8, pady=8)

        self._label_aviso = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
            fg_color=CORES.get("destaqueAvisoLegal", CORES["avisoFundo"]),
            corner_radius=8,
        )
        self._label_aviso.pack(fill="x", padx=16, pady=(0, 12))

    def _carregar_dados(self, forcar: bool = False) -> None:
        self._label_status.configure(text="Baixando cotacoes oficiais do Tesouro...")

        def tarefa():
            return self._controlador.obter_painel(forcar_atualizacao=forcar)

        def ao_concluir(resultado, erro_thread):
            if erro_thread:
                self._label_status.configure(text=f"Erro: {erro_thread}")
                messagebox.showerror("Tesouro Direto", erro_thread, parent=self)
                return
            if resultado is None:
                return

            painel, erro = resultado
            if erro:
                self._label_status.configure(text=erro)
                messagebox.showerror("Tesouro Direto", erro, parent=self)
                return
            if painel is None:
                self._label_status.configure(text="Nenhum titulo disponivel.")
                return

            self._titulos = painel.titulos
            self._label_status.configure(
                text=(
                    f"{len(painel.titulos)} titulos — cotacao de {painel.data_base_texto} "
                    f"({len(painel.familias)} familias)"
                )
            )
            self._label_aviso.configure(text=painel.aviso)
            self._montar_filtro_familias(["Todos", *painel.familias])
            self._preencher_tabela()

        executar_em_thread(self, tarefa, ao_concluir)

    def _montar_filtro_familias(self, familias: list[str]) -> None:
        for widget in self._frame_filtro.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self._frame_filtro,
            text="Filtrar por familia:",
            font=ctk.CTkFont(size=13),
            text_color=CORES["texto"],
        ).pack(side="left", padx=(0, 8))

        valores = familias if familias else ["Todos"]
        self._seletor_familia = ctk.CTkSegmentedButton(
            self._frame_filtro,
            values=valores,
            command=self._ao_mudar_familia,
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            selected_hover_color=CORES["primariaHover"],
            unselected_color=CORES["superficie"],
            unselected_hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        )
        if self._familia_selecionada not in valores:
            self._familia_selecionada = "Todos"
        self._seletor_familia.set(self._familia_selecionada)
        self._seletor_familia.pack(side="left", fill="x", expand=True)

    def _ao_mudar_familia(self, valor: str) -> None:
        self._familia_selecionada = valor
        self._preencher_tabela()

    def _preencher_tabela(self) -> None:
        if self._scroll_tabela is None:
            return

        for widget in self._scroll_tabela.winfo_children():
            widget.destroy()

        filtrados = self._titulos
        if self._familia_selecionada != "Todos":
            filtrados = [t for t in self._titulos if t.familia == self._familia_selecionada]

        if not filtrados:
            ctk.CTkLabel(
                self._scroll_tabela,
                text="Nenhum titulo nesta familia na cotacao atual.",
                font=ctk.CTkFont(size=13),
                text_color=CORES["textoSecundario"],
            ).pack(pady=24)
            return

        linhas: list[LinhaTabelaOrdenavel] = []
        for titulo in filtrados:
            prazo_venc = montar_prazo_legivel(data_fim=titulo.data_vencimento)
            linhas.append(
                LinhaTabelaOrdenavel(
                    valores=[
                        titulo.familia,
                        titulo.tipo_titulo,
                        montar_texto_celula_prazo(prazo_venc),
                        self._formatar_taxa(titulo.taxa_venda),
                        self._formatar_taxa(titulo.taxa_compra),
                        formatar_moeda(titulo.pu_venda) if titulo.pu_venda is not None else "—",
                        formatar_moeda(titulo.pu_compra) if titulo.pu_compra is not None else "—",
                    ],
                    chaves=[
                        titulo.familia,
                        titulo.tipo_titulo,
                        prazo_venc.dias_totais,
                        titulo.taxa_venda if titulo.taxa_venda is not None else -1.0,
                        titulo.taxa_compra if titulo.taxa_compra is not None else -1.0,
                        titulo.pu_venda if titulo.pu_venda is not None else -1.0,
                        titulo.pu_compra if titulo.pu_compra is not None else -1.0,
                    ],
                    ao_duplo_clique=lambda ident=titulo.identificador: self._abrir_detalhes(ident),
                )
            )

        renderizar_tabela_zebrada(
            self._scroll_tabela,
            self._COLUNAS,
            linhas,
            self._ordenacao_tabela,
            self._preencher_tabela,
        )

    @staticmethod
    def _formatar_taxa(valor: float | None) -> str:
        if valor is None:
            return "—"
        texto = f"{valor:.2f}".replace(".", ",")
        return f"{texto}%"

    def _abrir_detalhes(self, identificador: str) -> None:
        if self._janela_detalhes is not None:
            try:
                if self._janela_detalhes.winfo_exists():
                    self._janela_detalhes.focus_force()
                    return
            except Exception:
                pass

        self._janela_detalhes = JanelaDetalhesTesouro(self, self._controlador, identificador)
