"""Janela com historico de compras realizadas na carteira."""
from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import LinhaCompraCarteira
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread, janela_ui_ainda_ativa
from src.View.formatadores import formatar_moeda
from src.View.janela_editar_compra_carteira import abrir_editar_compra_carteira
from src.View.tabela_compras_carteira_helper import (
    aplicar_ajuste_altura_grid_compras,
    criar_grid_compras_carteira,
    liberar_grid_compras_carteira,
    obter_ids_selecionados_compras,
    obter_linha_compra_por_id,
    preencher_grid_compras_carteira,
)
from src.View.tema import CORES


class JanelaComprasCarteira(ctk.CTkToplevel):
    """Lista compras registradas com manutencao e valores da operacao."""

    def __init__(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        super().__init__(pai)
        self._janela_pai = pai
        self._controlador = ControladorCarteira()
        self._tabela: ttk.Treeview | None = None
        self._carregando = False

        self.title("Compras realizadas")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(1000, 620)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(200, self._carregar_dados)
        self.after(400, lambda: aplicar_ajuste_altura_grid_compras(self._tabela))

    def _montar_interface(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            cabecalho,
            text="Compras realizadas",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Historico de compras registradas na carteira. "
                "Edite ou remova compras; ao remover, a posicao correspondente "
                "tambem sai da carteira quando ainda existir."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=960,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self._painel_resumo = ctk.CTkFrame(
            cabecalho,
            fg_color=CORES.get("infoFundo", CORES["fundo"]),
            corner_radius=10,
            border_width=1,
            border_color=CORES["borda"],
        )
        self._painel_resumo.pack(fill="x", padx=16, pady=(0, 8))

        self._label_resumo = ctk.CTkLabel(
            self._painel_resumo,
            text="Carregando...",
            font=ctk.CTkFont(size=13),
            text_color=CORES["texto"],
            justify="left",
            anchor="w",
        )
        self._label_resumo.pack(anchor="w", padx=14, pady=10)

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))
        barra.grid_columnconfigure(0, weight=1)

        botoes = (
            ("Editar selecionado", self._editar_selecionado),
            ("Remover selecionados", self._remover_selecionados),
            ("Atualizar", self._carregar_dados),
        )
        for texto, comando in botoes:
            ctk.CTkButton(
                barra,
                text=texto,
                command=comando,
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=168,
                height=36,
            ).pack(side="left", padx=(0, 8))

        self._label_status = ctk.CTkLabel(
            barra,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            anchor="w",
            justify="left",
        )
        self._label_status.pack(side="left", padx=(12, 0), fill="x", expand=True)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._tabela = criar_grid_compras_carteira(
            container,
            "Compras registradas",
            altura=6,
            modo_tela_cheia=True,
            ao_duplo_clique=self._editar_selecionado,
        )

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

    def _carregar_dados(self) -> None:
        if self._carregando or not janela_ui_ainda_ativa(self):
            return
        self._carregando = True
        self._label_status.configure(text="Carregando compras...")

        def buscar():
            return self._controlador.obter_linhas_compras_carteira()

        def ao_concluir(resultado, erro_thread):
            self._carregando = False
            if not janela_ui_ainda_ativa(self):
                return
            if erro_thread:
                self._label_status.configure(text=f"Erro: {erro_thread}", text_color=CORES["erro"])
                return

            linhas, erro = resultado
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                return

            if self._tabela is not None:
                preencher_grid_compras_carteira(self._tabela, linhas)
            self._atualizar_resumo(linhas)
            aplicar_ajuste_altura_grid_compras(self._tabela)
            if linhas:
                self._label_status.configure(
                    text=f"{len(linhas)} compra(s) registrada(s).",
                    text_color=CORES["textoSecundario"],
                )
            else:
                self._label_status.configure(
                    text="Nenhuma compra registrada ainda. Use Registrar compra na carteira.",
                    text_color=CORES["textoSecundario"],
                )

        executar_em_thread(self, buscar, ao_concluir)

    def _editar_selecionado(self) -> None:
        selecionados = obter_ids_selecionados_compras(self._tabela)
        if len(selecionados) != 1:
            messagebox.showwarning(
                "Editar compra",
                "Selecione exatamente uma compra na grid.",
                parent=self,
            )
            return

        compra_id = selecionados[0]
        compra = self._controlador.obter_compra(compra_id)
        if compra is None:
            messagebox.showwarning("Editar compra", "Compra nao encontrada.", parent=self)
            return

        linha = obter_linha_compra_por_id(self._tabela, compra_id)
        moeda = linha.moeda if linha is not None else "BRL"
        na_carteira = linha.na_carteira if linha is not None else False
        abrir_editar_compra_carteira(
            self,
            self._controlador,
            compra,
            moeda=moeda,
            na_carteira=na_carteira,
            ao_salvar=self._carregar_dados,
        )

    def _remover_selecionados(self) -> None:
        selecionados = obter_ids_selecionados_compras(self._tabela)
        if not selecionados:
            messagebox.showwarning(
                "Remover compra",
                "Selecione uma ou mais compras na grid.",
                parent=self,
            )
            return

        quantidade = len(selecionados)
        texto = (
            "A compra sera removida do historico e a posicao correspondente "
            "saira da carteira, se ainda existir."
            if quantidade == 1
            else (
                f"As {quantidade} compras serao removidas do historico e as posicoes "
                "correspondentes sairao da carteira, quando existirem."
            )
        )
        if not messagebox.askyesno("Remover compra", texto, parent=self):
            return

        erros: list[str] = []
        for compra_id in selecionados:
            _, erro = self._controlador.remover_compra(compra_id)
            if erro:
                erros.append(erro)

        if erros:
            messagebox.showwarning(
                "Remover compra",
                "\n".join(erros[:5]),
                parent=self,
            )

        self._carregar_dados()

    def _atualizar_resumo(self, linhas: list[LinhaCompraCarteira]) -> None:
        if not linhas:
            self._label_resumo.configure(text="Nenhuma compra no historico.")
            return

        total_investido = sum(l.compra.valor_compra for l in linhas)
        na_carteira = sum(1 for l in linhas if l.na_carteira)
        fora = len(linhas) - na_carteira

        self._label_resumo.configure(
            text=(
                f"Total investido: {formatar_moeda(total_investido)}  ·  "
                f"Na carteira: {na_carteira}  ·  "
                f"Fora da carteira: {fora}"
            ),
        )

    def _ao_fechar(self) -> None:
        liberar_grid_compras_carteira(self._tabela)
        self.destroy()


def abrir_compras_carteira(pai: ctk.CTk | ctk.CTkToplevel) -> JanelaComprasCarteira | None:
    """Abre a tela de compras realizadas."""
    if not pai.winfo_exists():
        return None
    return JanelaComprasCarteira(pai)
