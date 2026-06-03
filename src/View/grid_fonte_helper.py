"""Seletor de tamanho da fonte das grids (grava no INI)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Model.opcoes_fonte_grid import FONTE_MEDIO, ROTULOS_FONTE_GRID
from src.Tool.config_painel import ConfigPainelIni
from src.View.tema import CORES


def criar_combo_fonte_grid(
    pai: ctk.CTkFrame,
    config: ConfigPainelIni,
    ao_mudar: Callable[[], None],
) -> ctk.CTkComboBox:
    """Combo pequeno/medio/grande — mesma ideia do seletor Fotos das noticias."""
    bloco = ctk.CTkFrame(pai, fg_color="transparent")
    bloco.pack(side="right", padx=(12, 0))

    ctk.CTkLabel(
        bloco,
        text="Fonte grid",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
    ).pack(anchor="w")

    rotulo_para_modo = {v: k for k, v in ROTULOS_FONTE_GRID.items()}
    valores_rotulo = list(ROTULOS_FONTE_GRID.values())
    modo_atual = config.carregar_fonte_grid()
    rotulo_atual = ROTULOS_FONTE_GRID.get(modo_atual, ROTULOS_FONTE_GRID[FONTE_MEDIO])

    def ao_selecionar(rotulo: str) -> None:
        modo = rotulo_para_modo.get(rotulo, modo_atual)
        try:
            config.salvar_fonte_grid(modo)
            ao_mudar()
        except OSError:
            pass

    combo = ctk.CTkComboBox(
        bloco,
        values=valores_rotulo,
        width=120,
        command=ao_selecionar,
    )
    combo.set(rotulo_atual)
    combo.pack(anchor="w", pady=(2, 0))
    return combo
