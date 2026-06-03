"""Seletor de tamanho das fotos nas telas de noticias (grava no INI)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Model.opcoes_fotos_noticias import ROTULOS_FOTOS
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.imagem_noticia_helper import limpar_cache_imagens_noticias
from src.View.tema import CORES


def criar_combo_fotos_noticias(
    pai: ctk.CTkFrame,
    config: ConfigPainelIni,
    ao_mudar: Callable[[], None],
) -> ctk.CTkComboBox:
    """Combo para escolher nenhum/pequeno/medio/grande e salvar em dados/painel.ini."""
    bloco = ctk.CTkFrame(pai, fg_color="transparent")
    bloco.pack(side="right", padx=(12, 0))

    ctk.CTkLabel(
        bloco,
        text="Fotos",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
    ).pack(anchor="w")

    rotulo_para_modo = {v: k for k, v in ROTULOS_FOTOS.items()}
    valores_rotulo = list(ROTULOS_FOTOS.values())
    modo_atual = config.carregar_fotos_noticias()
    from src.Model.opcoes_fotos_noticias import FOTOS_MEDIO

    rotulo_atual = ROTULOS_FOTOS.get(modo_atual, ROTULOS_FOTOS[FOTOS_MEDIO])

    def ao_selecionar(rotulo: str) -> None:
        modo = rotulo_para_modo.get(rotulo, modo_atual)
        try:
            config.salvar_fotos_noticias(modo)
            limpar_cache_imagens_noticias()
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
