"""Inferencia de tipo e normalizacao de simbolos para a carteira."""
from __future__ import annotations

import re

from src.Model.carteira import TipoAtivoCarteira
from src.Model.indices_universo import INDICES_MERCADO
from src.Model.resultado_busca import ResultadoBusca
from src.Tool.etfs_helper import eh_etf
from src.Tool.fiis_helper import eh_fii
from src.Tool.texto_busca_helper import normalizar_texto_busca
from src.Tool.validadores import (
    eh_simbolo_cripto_conhecido,
    normalizar_simbolo,
    normalizar_simbolo_cripto,
)


def simbolo_e_indice_carteira(simbolo: str) -> bool:
    """Indica se o ticker pertence ao universo de indices da carteira."""
    limpo = (simbolo or "").strip().upper()
    if not limpo:
        return False
    if limpo.startswith("^"):
        return True
    return any(indice.simbolo.upper() == limpo for indice in INDICES_MERCADO)


def inferir_tipo_ativo_carteira(simbolo: str) -> TipoAtivoCarteira:
    """Deduz o tipo do ativo a partir do simbolo Yahoo ou ticker digitado."""
    limpo = (simbolo or "").strip().upper()
    if not limpo:
        return "acoes"

    if simbolo_e_indice_carteira(limpo):
        return "indices"

    codigo_b3 = limpo.replace(".SA", "")
    if re.match(r"^[A-Z]{4}\d{1,2}$", codigo_b3):
        ticker_b3 = limpo if ".SA" in limpo else f"{codigo_b3}.SA"
        if eh_etf(ticker_b3):
            return "etfs"
        if eh_fii(ticker_b3):
            return "fiis"
        return "acoes"

    if eh_simbolo_cripto_conhecido(limpo):
        return "cripto"

    simbolo_acao, _ = normalizar_simbolo(simbolo)
    if simbolo_acao and eh_etf(simbolo_acao):
        return "etfs"
    if simbolo_acao and eh_fii(simbolo_acao):
        return "fiis"

    return "acoes"


def buscar_indices_por_termo(termo: str, limite: int = 12) -> list[ResultadoBusca]:
    """Filtra indices cadastrados pelo termo de busca."""
    termo_norm = normalizar_texto_busca(termo).upper()
    if not termo_norm:
        return []

    resultados: list[ResultadoBusca] = []
    for indice in INDICES_MERCADO:
        texto = normalizar_texto_busca(
            f"{indice.simbolo} {indice.nome} {indice.regiao}"
        ).upper()
        if termo_norm in texto or termo_norm in indice.simbolo.upper():
            resultados.append(
                ResultadoBusca(
                    simbolo=indice.simbolo,
                    nome=indice.nome,
                    bolsa=indice.regiao,
                )
            )
        if len(resultados) >= limite:
            break
    return resultados


def normalizar_simbolo_carteira(
    entrada: str,
    tipo: TipoAtivoCarteira | None = None,
) -> tuple[str | None, TipoAtivoCarteira | None, str | None]:
    """
    Normaliza codigo digitado e retorna (simbolo, tipo, erro).
    Sem tipo informado, infere automaticamente.
    """
    texto = (entrada or "").strip()
    if not texto:
        return None, None, "Informe o codigo do ativo."

    if tipo == "cripto":
        simbolo, erro = normalizar_simbolo_cripto(texto)
        if erro or not simbolo:
            return None, None, erro
        return simbolo, "cripto", None

    if tipo == "indices":
        simbolo, erro = normalizar_simbolo(texto)
        if erro or not simbolo:
            return None, None, erro
        if not simbolo_e_indice_carteira(simbolo):
            return None, None, "Codigo nao pertence a um indice cadastrado."
        return simbolo, "indices", None

    if tipo in ("acoes", "fiis", "etfs"):
        simbolo, erro = normalizar_simbolo(texto)
        if erro or not simbolo:
            return None, None, erro
        tipo_inferido = inferir_tipo_ativo_carteira(simbolo)
        if tipo == "fiis" and tipo_inferido != "fiis":
            return None, None, "Codigo informado nao e um FII."
        if tipo == "etfs" and tipo_inferido != "etfs":
            return None, None, "Codigo informado nao e um ETF."
        if tipo == "acoes" and tipo_inferido not in ("acoes", "fiis", "etfs"):
            return None, None, "Codigo informado nao e uma acao."
        return simbolo, tipo_inferido if tipo is None else tipo, None

    # Deteccao automatica (sem tipo fixo): acoes/indices/FII antes de cripto.
    simbolo_acao, erro_acao = normalizar_simbolo(texto)
    if simbolo_acao:
        return simbolo_acao, inferir_tipo_ativo_carteira(simbolo_acao), None

    simbolo_cripto, erro_cripto = normalizar_simbolo_cripto(texto)
    if simbolo_cripto and erro_cripto is None:
        tipo_cripto = inferir_tipo_ativo_carteira(simbolo_cripto)
        if tipo_cripto == "cripto":
            return simbolo_cripto, tipo_cripto, None

    return None, None, erro_acao or erro_cripto or "Codigo invalido."
