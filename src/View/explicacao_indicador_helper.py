"""Painel expansivel com explicacao do indicador (botao ? + Fechar)."""
from __future__ import annotations

import customtkinter as ctk

from src.View.tema import CORES


class GerenciadorExplicacaoIndicadores:
    """Garante que apenas um painel de explicacao fique aberto por vez."""

    def __init__(self) -> None:
        self._painel_aberto: ctk.CTkFrame | None = None

    def fechar_todos(self) -> None:
        if self._painel_aberto is not None:
            try:
                if self._painel_aberto.winfo_exists():
                    self._painel_aberto.destroy()
            except Exception:
                pass
            self._painel_aberto = None

    def alternar(
        self,
        card: ctk.CTkFrame,
        rotulo: str,
        explicacao: str,
        calculo: str | None = None,
    ) -> None:
        if not explicacao.strip() and not (calculo or "").strip():
            return

        if self._painel_aberto is not None:
            try:
                if (
                    self._painel_aberto.winfo_exists()
                    and self._painel_aberto.master == card
                ):
                    self.fechar_todos()
                    return
            except Exception:
                pass
            self.fechar_todos()

        painel = ctk.CTkFrame(
            card,
            fg_color=CORES.get("infoFundo", CORES["fundo"]),
            corner_radius=8,
            border_width=1,
            border_color=CORES["primaria"],
        )
        painel.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(
            painel,
            text=rotulo,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["primaria"],
            anchor="w",
            justify="left",
        ).pack(anchor="w", padx=10, pady=(8, 4))

        if explicacao.strip():
            ctk.CTkLabel(
                painel,
                text="O que significa",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=CORES["textoSecundario"],
                anchor="w",
            ).pack(anchor="w", padx=10, pady=(0, 2))

            ctk.CTkLabel(
                painel,
                text=explicacao,
                font=ctk.CTkFont(size=13),
                text_color=CORES["texto"],
                wraplength=400,
                justify="left",
                anchor="w",
            ).pack(anchor="w", padx=10, pady=(0, 8))

        if calculo and calculo.strip():
            ctk.CTkLabel(
                painel,
                text="Como foi calculado",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=CORES["textoSecundario"],
                anchor="w",
            ).pack(anchor="w", padx=10, pady=(4, 2))

            ctk.CTkLabel(
                painel,
                text=calculo,
                font=ctk.CTkFont(size=12),
                text_color=CORES["texto"],
                wraplength=400,
                justify="left",
                anchor="w",
            ).pack(anchor="w", padx=10, pady=(0, 8))

        ctk.CTkButton(
            painel,
            text="Fechar",
            width=80,
            height=28,
            command=self.fechar_todos,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(anchor="e", padx=10, pady=(0, 8))

        self._painel_aberto = painel


def adicionar_botao_explicacao_indicador(
    card: ctk.CTkFrame,
    rotulo: str,
    explicacao: str,
    gerenciador: GerenciadorExplicacaoIndicadores,
    calculo: str | None = None,
) -> None:
    """Coloca botao pequeno no card; ao clicar, abre painel com explicacao e calculo."""
    if not explicacao.strip() and not (calculo or "").strip():
        return

    linha_topo = ctk.CTkFrame(card, fg_color="transparent")
    linha_topo.pack(fill="x", padx=10, pady=(8, 0))

    ctk.CTkLabel(
        linha_topo,
        text=rotulo,
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=CORES["textoSecundario"],
        anchor="w",
    ).pack(side="left", fill="x", expand=True)

    ctk.CTkButton(
        linha_topo,
        text="?",
        width=30,
        height=26,
        font=ctk.CTkFont(size=14, weight="bold"),
        command=lambda: gerenciador.alternar(card, rotulo, explicacao, calculo),
        fg_color=CORES["primaria"],
        hover_color=CORES["primariaHover"],
    ).pack(side="right")
