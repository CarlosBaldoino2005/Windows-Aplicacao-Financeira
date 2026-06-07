"""Janela de acoes favoritas com grid de cotacoes e persistencia local."""
from __future__ import annotations

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
from tkinter import ttk

from src.Controller.controlador_mercado import ControladorMercado
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.Tool.validadores import normalizar_simbolo, normalizar_simbolo_cripto
from src.View.placeholders_ui import (
    PLACEHOLDER_BUSCA_ACAO,
    PLACEHOLDER_BUSCA_CRIPTO,
    PLACEHOLDER_CODIGO_ACAO,
    PLACEHOLDER_CODIGO_CRIPTO,
)
from src.View.grid_fonte_helper import criar_combo_fonte_grid
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.tabela_mercado_helper import (
    criar_card_tabela,
    preencher_tabela,
    reaplicar_fonte_em_tabelas,
)
from src.View.tema import CORES


class JanelaFavoritas(ctk.CTkToplevel):
    """Lista favoritas salvas em disco com cotacoes atualizadas."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: ControladorMercado,
        modo_cripto: bool = False,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._modo_cripto = modo_cripto
        self._config_painel = ConfigPainelIni()
        self._janela_grafico: JanelaGraficoAcao | None = None
        self._tabela: ttk.Treeview | None = None

        self.title("Criptos favoritas" if modo_cripto else "Acoes favoritas")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(820, 560)

        self._montar_interface()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(250, self._atualizar_grid)

    def _ao_fechar(self) -> None:
        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass
        self.destroy()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Criptos favoritas" if self._modo_cripto else "Acoes favoritas",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Adicione criptomoedas que deseja acompanhar. A lista fica salva neste computador."
                if self._modo_cripto
                else "Adicione acoes que deseja acompanhar. A lista fica salva neste computador."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=16, pady=(0, 8))

        linha_add = ctk.CTkFrame(cabecalho, fg_color="transparent")
        linha_add.pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkLabel(linha_add, text="Codigo ou nome").pack(side="left", padx=(0, 8))
        self._entrada_busca = ctk.CTkEntry(
            linha_add,
            width=260,
            placeholder_text=(
                PLACEHOLDER_BUSCA_CRIPTO if self._modo_cripto else PLACEHOLDER_BUSCA_ACAO
            ),
        )
        self._entrada_busca.pack(side="left", padx=(0, 8))
        self._entrada_busca.bind("<Return>", lambda _e: self._pesquisar())

        ctk.CTkButton(
            linha_add,
            text="Buscar",
            command=self._pesquisar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(linha_add, text="ou codigo").pack(side="left", padx=(8, 8))
        self._entrada_codigo = ctk.CTkEntry(
            linha_add,
            width=100,
            placeholder_text=(
                PLACEHOLDER_CODIGO_CRIPTO if self._modo_cripto else PLACEHOLDER_CODIGO_ACAO
            ),
        )
        self._entrada_codigo.pack(side="left", padx=(0, 8))
        self._entrada_codigo.bind("<Return>", lambda _e: self._adicionar_codigo())

        ctk.CTkButton(
            linha_add,
            text="Adicionar",
            command=self._adicionar_codigo,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="left")

        self._frame_resultados = ctk.CTkScrollableFrame(
            cabecalho, height=90, fg_color=CORES["fundo"], label_text="Resultados da busca"
        )
        self._frame_resultados.pack(fill="x", padx=16, pady=(4, 8))

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))

        self._label_status = ctk.CTkLabel(
            barra, text="", font=ctk.CTkFont(size=12), text_color=CORES["textoSecundario"]
        )
        self._label_status.pack(side="left")

        ctk.CTkButton(
            barra,
            text="Remover selecionada",
            command=self._remover_selecionada,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=150,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            barra,
            text="Atualizar cotacoes",
            command=self._atualizar_grid,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="right")

        criar_combo_fonte_grid(barra, self._config_painel, self._ao_mudar_fonte_grid)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._tabela = criar_card_tabela(
            container,
            (
                "Suas criptos favoritas (duplo clique abre o grafico)"
                if self._modo_cripto
                else "Suas acoes favoritas (duplo clique abre o grafico)"
            ),
            altura=14,
            ao_duplo_clique=self._ao_duplo_clique,
            expandir=True,
        )

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=120,
        ).pack(side="right")

    def _limpar_resultados(self) -> None:
        for widget in self._frame_resultados.winfo_children():
            widget.destroy()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _pesquisar(self) -> None:
        termo = self._entrada_busca.get().strip()
        if not termo:
            aviso = (
                "Digite o nome ou codigo da criptomoeda (ex.: Bitcoin ou SOL)."
                if self._modo_cripto
                else "Digite o nome ou codigo da acao."
            )
            messagebox.showwarning("Buscar", aviso, parent=self)
            return

        status = (
            "Buscando criptomoedas..."
            if self._modo_cripto
            else "Buscando acoes..."
        )
        self._label_status.configure(text=status)

        def buscar():
            return self._controlador.pesquisar_acoes(termo)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                self._limpar_resultados()
                return
            itens, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                self._limpar_resultados()
                return
            self._exibir_resultados(itens)
            self._label_status.configure(
                text=f"{len(itens)} resultado(s). Clique em Adicionar na linha desejada.",
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _exibir_resultados(self, itens) -> None:
        self._limpar_resultados()
        if not itens:
            ctk.CTkLabel(
                self._frame_resultados,
                text="Nenhum resultado.",
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=4, pady=4)
            return

        for item in itens:
            linha = ctk.CTkFrame(self._frame_resultados, fg_color=CORES["superficie"], corner_radius=8)
            linha.pack(fill="x", padx=4, pady=3)

            codigo = self._codigo_exibicao(item.simbolo)
            texto = f"{codigo}  —  {item.nome}  ({item.bolsa})"
            ctk.CTkLabel(
                linha,
                text=texto,
                anchor="w",
                font=ctk.CTkFont(size=12),
                text_color=CORES["texto"],
            ).pack(side="left", fill="x", expand=True, padx=8, pady=6)

            ctk.CTkButton(
                linha,
                text="Adicionar",
                width=90,
                command=lambda s=item.simbolo: self._adicionar_favorito(s),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
            ).pack(side="right", padx=8, pady=4)

    def _normalizar_entrada(self, termo: str):
        if self._modo_cripto:
            return normalizar_simbolo_cripto(termo)
        return normalizar_simbolo(termo)

    def _codigo_exibicao(self, simbolo: str) -> str:
        if self._modo_cripto:
            return simbolo.replace("-USD", "")
        return simbolo.replace(".SA", "")

    def _adicionar_codigo(self) -> None:
        termo = self._entrada_codigo.get().strip() or self._entrada_busca.get().strip()
        if not termo:
            aviso = (
                "Informe o codigo da criptomoeda (ex.: BTC ou Bitcoin)."
                if self._modo_cripto
                else "Informe o codigo da acao."
            )
            messagebox.showwarning("Adicionar", aviso, parent=self)
            return
        simbolo, erro = self._normalizar_entrada(termo)
        if erro:
            messagebox.showwarning("Adicionar", erro, parent=self)
            return
        self._adicionar_favorito(simbolo)

    def _adicionar_favorito(self, simbolo: str) -> None:
        ok, msg = self._controlador.adicionar_favorito(simbolo)
        if not ok:
            messagebox.showwarning("Favoritos", msg or "Nao foi possivel adicionar.", parent=self)
            return

        codigo = self._codigo_exibicao(simbolo)
        self._entrada_codigo.delete(0, "end")
        self._label_status.configure(
            text=f"{codigo} adicionada aos favoritos.",
            text_color=CORES["sucesso"],
        )
        self._atualizar_grid()

    def _remover_selecionada(self) -> None:
        if not self._tabela:
            return
        selecao = self._tabela.selection()
        if not selecao:
            aviso = (
                "Selecione uma criptomoeda na lista."
                if self._modo_cripto
                else "Selecione uma acao na lista."
            )
            messagebox.showinfo("Remover", aviso, parent=self)
            return

        simbolo = selecao[0]
        ok, msg = self._controlador.remover_favorito(simbolo)
        if not ok:
            messagebox.showwarning("Favoritos", msg or "Nao foi possivel remover.", parent=self)
            return

        self._label_status.configure(
            text=f"{self._codigo_exibicao(simbolo)} removida dos favoritos.",
            text_color=CORES["sucesso"],
        )
        self._atualizar_grid()

    def _ao_mudar_fonte_grid(self) -> None:
        if self._tabela is not None:
            reaplicar_fonte_em_tabelas([self._tabela])

    def _atualizar_grid(self) -> None:
        if not self._tabela:
            return

        simbolos = self._controlador.listar_simbolos_favoritos()
        if not simbolos:
            preencher_tabela(self._tabela, [])
            self._label_status.configure(
                text=(
                    "Nenhuma cripto favorita. Use Buscar ou Adicionar acima."
                    if self._modo_cripto
                    else "Nenhuma acao favorita. Use Buscar ou Adicionar acima."
                ),
                text_color=CORES["textoSecundario"],
            )
            return

        self._label_status.configure(text="Atualizando cotacoes...")

        def buscar():
            return self._controlador.obter_cotacoes_favoritas()

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                return
            cotacoes, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                return
            preencher_tabela(self._tabela, cotacoes)
            hora = datetime.now().strftime("%H:%M:%S")
            self._label_status.configure(
                text=f"{len(cotacoes)} favorita(s) — atualizado as {hora}",
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _ao_duplo_clique(self, evento) -> None:
        widget = evento.widget
        selecao = widget.selection()
        if not selecao:
            return
        self._abrir_grafico(selecao[0])

    def _abrir_grafico(self, simbolo: str) -> None:
        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass

        self._janela_grafico = JanelaGraficoAcao(self, self._controlador, simbolo)
