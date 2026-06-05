"""Seletor de servidor de noticias (grava no INI e recarrega a lista)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Model.provedores_noticias import (
    CATEGORIA_CRIPTO,
    CATEGORIA_MERCADO,
    chave_por_rotulo,
    listar_provedores,
    resolver_provedor,
    rotulo_por_chave,
)
from src.Tool.config_painel import ConfigPainelIni
from src.View.tema import CORES


def criar_combo_provedor_noticias(
    pai: ctk.CTkFrame,
    config: ConfigPainelIni,
    ao_mudar: Callable[[str], None],
    modo_cripto: bool = False,
) -> ctk.CTkComboBox:
    """Combo com servidores Brasil/EUA/mundo ou cripto; persiste em dados/painel.ini."""
    categoria = CATEGORIA_CRIPTO if modo_cripto else CATEGORIA_MERCADO
    bloco = ctk.CTkFrame(pai, fg_color="transparent")
    bloco.pack(side="right", padx=(12, 0))

    ctk.CTkLabel(
        bloco,
        text="Servidor",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
    ).pack(anchor="w")

    provedores = listar_provedores(categoria)
    rotulos = [p.nome for p in provedores]
    if modo_cripto:
        chave_atual = config.carregar_provedor_noticias_cripto()
    else:
        chave_atual = config.carregar_provedor_noticias()
    rotulo_atual = rotulo_por_chave(chave_atual, categoria)

    def ao_selecionar(rotulo: str) -> None:
        chave = chave_por_rotulo(rotulo, categoria)
        try:
            if modo_cripto:
                config.salvar_provedor_noticias_cripto(chave)
            else:
                config.salvar_provedor_noticias(chave)
            ao_mudar(chave)
        except OSError:
            pass

    combo = ctk.CTkComboBox(
        bloco,
        values=rotulos,
        width=200,
        command=ao_selecionar,
    )
    if rotulo_atual in rotulos:
        combo.set(rotulo_atual)
    elif rotulos:
        combo.set(rotulos[0])
    combo.pack(anchor="w", pady=(2, 0))
    return combo


def descricao_provedor_atual(config: ConfigPainelIni, modo_cripto: bool = False) -> str:
    categoria = CATEGORIA_CRIPTO if modo_cripto else CATEGORIA_MERCADO
    if modo_cripto:
        chave = config.carregar_provedor_noticias_cripto()
    else:
        chave = config.carregar_provedor_noticias()
    provedor = resolver_provedor(chave, categoria)
    return f"Servidor: {provedor.nome} — {provedor.descricao}"
