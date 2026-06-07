"""Carrega e persiste o valor padrao de simulacao (painel.ini) nos campos monetarios."""
from __future__ import annotations

import customtkinter as ctk

from src.Tool.config_painel import ConfigPainelIni
from src.Tool.mascara_moeda_helper import formatar_centavos_ptbr
from src.Tool.validadores import validar_valor_monetario_ptbr


def texto_valor_simulacao_ptbr(valor: float, prefixo: str = "R$ ") -> str:
    """Formata valor decimal para exibicao no campo de simulacao."""
    prefixo = prefixo if prefixo.endswith(" ") else f"{prefixo} "
    centavos = max(0, int(round(valor * 100)))
    return f"{prefixo}{formatar_centavos_ptbr(centavos)}"


def preencher_entrada_valor_simulacao(
    entry: ctk.CTkEntry,
    config: ConfigPainelIni,
    prefixo: str = "R$ ",
) -> None:
    """Preenche o campo com o valor salvo no INI (padrao R$ 10.000,00)."""
    valor = config.carregar_valor_simulacao_renda_fixa()
    entry.delete(0, "end")
    entry.insert(0, texto_valor_simulacao_ptbr(valor, prefixo))


def persistir_valor_simulacao_da_entrada(
    entry: ctk.CTkEntry,
    config: ConfigPainelIni,
) -> bool:
    """Grava no INI se o texto do campo for um valor monetario valido."""
    valor, erro = validar_valor_monetario_ptbr(entry.get())
    if erro or valor is None:
        return False
    try:
        config.salvar_valor_simulacao_renda_fixa(valor)
    except OSError:
        return False
    return True


def vincular_persistencia_valor_simulacao(
    entry: ctk.CTkEntry,
    config: ConfigPainelIni,
) -> None:
    """Salva no INI quando o usuario altera o valor (debounce, foco ou Enter)."""
    timer_id: list[str | None] = [None]

    def persistir(_evento=None) -> None:
        persistir_valor_simulacao_da_entrada(entry, config)

    def ao_soltar_tecla(_evento=None) -> None:
        if timer_id[0] is not None:
            entry.after_cancel(timer_id[0])
        timer_id[0] = entry.after(600, persistir)

    entry.bind("<FocusOut>", persistir, add="+")
    entry.bind("<Return>", persistir, add="+")
    entry.bind("<KeyRelease>", ao_soltar_tecla, add="+")


def configurar_entrada_valor_simulacao(
    entry: ctk.CTkEntry,
    config: ConfigPainelIni,
    prefixo: str = "R$ ",
) -> None:
    """Preenche com valor do INI e passa a gravar alteracoes automaticamente."""
    preencher_entrada_valor_simulacao(entry, config, prefixo)
    vincular_persistencia_valor_simulacao(entry, config)
