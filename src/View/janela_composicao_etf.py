"""Tela com os principais ativos que compoem a carteira de um ETF."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk

from src.Model.composicao_etf import ComposicaoEtf
from src.Service.composicao_etf_servico import ComposicaoEtfServico
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread
from src.View.tabela_composicao_etf_helper import (
    criar_grid_composicao_etf,
    liberar_grid_composicao_etf,
    preencher_grid_composicao_etf,
)
from src.View.tema import CORES


class JanelaComposicaoEtf(ctk.CTkToplevel):
    """Lista ordenavel das principais posicoes do ETF."""

    def __init__(self, pai: ctk.CTk, simbolo: str) -> None:
        super().__init__(pai)
        self._simbolo = simbolo
        self._servico = ComposicaoEtfServico()
        self._composicao: ComposicaoEtf | None = None
        self._tabela: ttk.Treeview | None = None

        codigo = codigo_exibicao(simbolo)
        self.title(f"Composicao da carteira — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 600)

        self._frame_conteudo = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_conteudo.pack(fill="both", expand=True, padx=16, pady=(12, 8))
        self._frame_conteudo.grid_columnconfigure(0, weight=1)
        self._frame_conteudo.grid_rowconfigure(3, weight=1)

        self._label_status = ctk.CTkLabel(
            self._frame_conteudo,
            text="Carregando composicao da carteira...",
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.grid(row=0, column=0, sticky="w", padx=4, pady=20)

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(100, self._carregar_em_thread)

    def _ao_fechar(self) -> None:
        liberar_grid_composicao_etf(self._tabela)
        self.destroy()

    def _carregar_em_thread(self) -> None:
        executar_em_thread(
            self,
            lambda: self._servico.obter_composicao(self._simbolo),
            self._ao_carregar,
        )

    def _ao_carregar(
        self,
        resultado: tuple[ComposicaoEtf | None, str | None] | None,
        erro_thread: str | None,
    ) -> None:
        if erro_thread:
            self._label_status.configure(
                text=f"Erro ao carregar: {erro_thread}",
                text_color=CORES["erro"],
            )
            return

        composicao, erro = resultado or (None, "Resposta invalida.")
        if erro or composicao is None:
            self._label_status.configure(
                text=erro or "Composicao indisponivel.",
                text_color=CORES["erro"],
            )
            return

        self._composicao = composicao
        self._exibir_composicao()

    def _exibir_composicao(self) -> None:
        for widget in self._frame_conteudo.winfo_children():
            widget.destroy()

        composicao = self._composicao
        if composicao is None:
            return

        self._frame_conteudo.grid_columnconfigure(0, weight=1)

        codigo = codigo_exibicao(composicao.simbolo_etf)
        ctk.CTkLabel(
            self._frame_conteudo,
            text=f"{codigo} — {composicao.nome_etf}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
            justify="left",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 6))

        subtitulo = (
            f"Principais posicoes reportadas ({composicao.fonte}). "
            "Percentuais podem refletir apenas o top 10 da fonte."
        )
        if composicao.simbolo_consultado and composicao.simbolo_consultado != composicao.simbolo_etf:
            ref = codigo_exibicao(composicao.simbolo_consultado)
            subtitulo += f" Referencia consultada: {ref}."

        ctk.CTkLabel(
            self._frame_conteudo,
            text=subtitulo,
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            anchor="w",
            justify="left",
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 8))

        linha_aviso = 2
        if composicao.aviso:
            ctk.CTkLabel(
                self._frame_conteudo,
                text=composicao.aviso,
                font=ctk.CTkFont(size=12),
                text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
                fg_color=CORES.get("destaqueAvisoLegal", CORES["avisoFundo"]),
                corner_radius=8,
                anchor="w",
                justify="left",
            ).grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 10))
            linha_aviso = 3

        self._frame_conteudo.grid_rowconfigure(linha_aviso, weight=1)

        container_grid = ctk.CTkFrame(self._frame_conteudo, fg_color="transparent")
        container_grid.grid(row=linha_aviso, column=0, sticky="nsew", padx=0, pady=(0, 4))
        container_grid.grid_columnconfigure(0, weight=1)
        container_grid.grid_rowconfigure(0, weight=1)

        frame_grid = ctk.CTkFrame(container_grid, fg_color="transparent")
        frame_grid.grid(row=0, column=0, sticky="nsew")
        frame_grid.grid_columnconfigure(0, weight=1)
        frame_grid.grid_rowconfigure(0, weight=1)

        self._tabela = criar_grid_composicao_etf(
            frame_grid,
            "Principais ativos da carteira",
            altura=max(10, len(composicao.ativos)),
        )
        preencher_grid_composicao_etf(self._tabela, composicao.ativos)

        ctk.CTkLabel(
            self._frame_conteudo,
            text="Dados publicos (Yahoo Finance). Uso educacional — nao e recomendacao de investimento.",
            font=ctk.CTkFont(size=11),
            text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
            anchor="w",
        ).grid(row=linha_aviso + 1, column=0, sticky="w", padx=4, pady=(8, 0))
