"""Confirmacao ao cadastrar ativo que esta na Black List."""
from __future__ import annotations

import customtkinter as ctk

from src.Model.carteira import ResultadoBuscaCarteira, ROTULOS_TIPO_CARTEIRA
from src.Service.blacklist_ativos_servico import BlacklistAtivosServico, normalizar_simbolo_blacklist
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.View import mensagem_helper as messagebox

_servico: BlacklistAtivosServico | None = None


def _obter_servico() -> BlacklistAtivosServico:
    global _servico
    if _servico is None:
        _servico = BlacklistAtivosServico()
    return _servico


def validar_ativo_existe_blacklist(
    termo: str,
    *,
    controlador=None,
) -> tuple[str | None, str | None]:
    """
    Confirma se o ativo existe na busca de mercado.
    Retorna (simbolo_normalizado, erro).
    """
    from src.Controller.controlador_carteira import ControladorCarteira as CtrlCarteira

    texto = (termo or "").strip()
    if not texto:
        return None, "Informe o codigo ou nome do ativo."

    ctrl = controlador or CtrlCarteira()
    resultados, msg = ctrl.pesquisar_ativos_automatico(texto)
    if not resultados:
        return None, msg or "Ativo nao encontrado. Use Buscar para localizar o codigo correto."

    simbolo_norm, _ = normalizar_simbolo_blacklist(texto)
    if simbolo_norm:
        for item in resultados:
            if item.simbolo == simbolo_norm:
                return item.simbolo, None
        codigo_busca = codigo_exibicao(simbolo_norm).upper()
        for item in resultados:
            if codigo_exibicao(item.simbolo).upper() == codigo_busca:
                return item.simbolo, None

    if len(resultados) == 1:
        return resultados[0].simbolo, None

    return None, "Varios resultados encontrados. Use Buscar e selecione o ativo na lista."


def rotulo_resultado_busca_blacklist(item: ResultadoBuscaCarteira) -> str:
    """Texto exibido na lista de resultados da busca."""
    simbolo = codigo_exibicao(item.simbolo)
    tipo = ROTULOS_TIPO_CARTEIRA[item.tipo_ativo]
    nome = (item.nome or "").strip()
    if nome:
        return f"{simbolo} — {nome} ({tipo})"
    return f"{simbolo} ({tipo})"


def confirmar_cadastro_blacklist(
    simbolo: str,
    *,
    parent: ctk.CTk | ctk.CTkToplevel | None = None,
) -> bool:
    """
    Retorna True se o cadastro pode prosseguir.
    Quando o ativo esta na Black List, pergunta se o usuario deseja continuar.
    """
    if not _obter_servico().esta_na_lista(simbolo):
        return True

    codigo = codigo_exibicao(simbolo)
    return messagebox.askyesno(
        "Black List",
        f"O ativo {codigo} esta na Black List.\nDeseja continuar mesmo assim?",
        parent=parent,
    )
