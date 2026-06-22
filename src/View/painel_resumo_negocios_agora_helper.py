"""Barra de resumo Comprar / Neutro / Vender da fita de negocios."""
from __future__ import annotations

import customtkinter as ctk

from src.Model.negocio_agora import ResumoNegociosAgora
from src.View.formatadores import formatar_inteiro_ptbr
from src.View.tema import CORES


class PainelResumoNegociosAgora(ctk.CTkFrame):
    """Resumo visual de proporcoes de compra, neutro e venda."""

    def __init__(self, pai: ctk.CTkBaseClass) -> None:
        super().__init__(pai, fg_color=CORES.get("infoFundo", CORES["superficie"]), corner_radius=10)
        self.grid_columnconfigure(0, weight=1)

        titulo = ctk.CTkLabel(
            self,
            text="Proporcao Compra / Venda",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
        )
        titulo.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        self._frame_barra = ctk.CTkFrame(self, fg_color=CORES["borda"], corner_radius=6, height=14)
        self._frame_barra.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        self._frame_barra.grid_columnconfigure(0, weight=1)
        self._frame_barra.grid_columnconfigure(1, weight=1)
        self._frame_barra.grid_columnconfigure(2, weight=1)
        self._frame_barra.grid_propagate(False)

        self._barra_compra = ctk.CTkFrame(self._frame_barra, fg_color=CORES["sucesso"], corner_radius=0, height=14)
        self._barra_neutro = ctk.CTkFrame(
            self._frame_barra,
            fg_color=CORES["textoSecundario"],
            corner_radius=0,
            height=14,
        )
        self._barra_venda = ctk.CTkFrame(self._frame_barra, fg_color=CORES["erro"], corner_radius=0, height=14)
        self._barra_compra.grid(row=0, column=0, sticky="nsew")
        self._barra_neutro.grid(row=0, column=1, sticky="nsew")
        self._barra_venda.grid(row=0, column=2, sticky="nsew")

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        linha.grid_columnconfigure(0, weight=1)
        linha.grid_columnconfigure(1, weight=1)
        linha.grid_columnconfigure(2, weight=1)

        self._label_compra = ctk.CTkLabel(
            linha,
            text="Comprar: 0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["sucesso"],
            anchor="w",
        )
        self._label_neutro = ctk.CTkLabel(
            linha,
            text="Neutro: 0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["textoSecundario"],
            anchor="center",
        )
        self._label_venda = ctk.CTkLabel(
            linha,
            text="Vender: 0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["erro"],
            anchor="e",
        )
        self._label_compra.grid(row=0, column=0, sticky="w")
        self._label_neutro.grid(row=0, column=1, sticky="ew")
        self._label_venda.grid(row=0, column=2, sticky="e")

    def atualizar(self, resumo: ResumoNegociosAgora) -> None:
        peso_compra = max(resumo.compra, 0)
        peso_neutro = max(resumo.neutro, 0)
        peso_venda = max(resumo.venda, 0)

        self._frame_barra.grid_columnconfigure(0, weight=peso_compra or 0)
        self._frame_barra.grid_columnconfigure(1, weight=peso_neutro or 0)
        self._frame_barra.grid_columnconfigure(2, weight=peso_venda or 0)
        if peso_compra == peso_neutro == peso_venda == 0:
            self._frame_barra.grid_columnconfigure(0, weight=1)
            self._frame_barra.grid_columnconfigure(1, weight=1)
            self._frame_barra.grid_columnconfigure(2, weight=1)

        self._label_compra.configure(text=f"Comprar: {formatar_inteiro_ptbr(resumo.compra)}")
        self._label_neutro.configure(text=f"Neutro: {formatar_inteiro_ptbr(resumo.neutro)}")
        self._label_venda.configure(text=f"Vender: {formatar_inteiro_ptbr(resumo.venda)}")

        if resumo.total == 0:
            self._label_compra.configure(text="Comprar: 0")
            self._label_neutro.configure(text="Neutro: 0")
            self._label_venda.configure(text="Vender: 0")
