"""Ordenacao de colunas nas grids (clique no cabecalho alterna asc/desc)."""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

SUFIXO_ASCENDENTE = " \u25b2"
SUFIXO_DESCENDENTE = " \u25bc"


@dataclass
class EstadoOrdenacaoColuna:
    """Indice da coluna ordenada e direcao (False = ascendente)."""

    indice: int | None = None
    descendente: bool = False

    def alternar(self, indice_coluna: int) -> None:
        if self.indice == indice_coluna:
            self.descendente = not self.descendente
        else:
            self.indice = indice_coluna
            self.descendente = False


@dataclass
class LinhaTabelaOrdenavel:
    """Linha zebrada com chaves de ordenacao por coluna."""

    valores: list[str]
    chaves: list[Any]
    cores_celulas: list[str] | None = None
    ao_duplo_clique: Callable[[], None] | None = None


def titulo_coluna_ordenada(
    texto_base: str,
    indice: int,
    estado: EstadoOrdenacaoColuna | None,
) -> str:
    if estado is None or estado.indice != indice:
        return texto_base
    sufixo = SUFIXO_DESCENDENTE if estado.descendente else SUFIXO_ASCENDENTE
    return f"{texto_base}{sufixo}"


def ordenar_linhas_tabela(
    linhas: list[LinhaTabelaOrdenavel],
    estado: EstadoOrdenacaoColuna | None,
) -> list[LinhaTabelaOrdenavel]:
    if estado is None or estado.indice is None or not linhas:
        return linhas
    indice = estado.indice

    def chave_linha(linha: LinhaTabelaOrdenavel) -> tuple:
        if indice < len(linha.chaves):
            return chave_comparavel(linha.chaves[indice])
        return chave_comparavel("")

    return sorted(linhas, key=chave_linha, reverse=estado.descendente)


def chave_comparavel(valor: Any) -> tuple:
    """Normaliza tipos comuns (numero, data pt-BR, moeda, texto) para sort estavel."""
    if valor is None:
        return (4, 0.0, "")

    if isinstance(valor, bool):
        return (0, float(valor), "")

    if isinstance(valor, (int, float)):
        return (0, float(valor), "")

    if hasattr(valor, "toordinal"):
        try:
            return (1, float(valor.toordinal()), "")
        except Exception:
            pass

    texto = str(valor).strip()
    if not texto or texto == "—":
        return (4, 0.0, "")

    data_ordinal = _extrair_data_ordinal(texto)
    if data_ordinal is not None:
        return (1, float(data_ordinal), "")

    numero = _extrair_numero_ptbr(texto)
    if numero is not None:
        return (0, numero, "")

    return (3, 0.0, texto.lower())


def _extrair_data_ordinal(texto: str) -> int | None:
    limpo = texto.strip()
    if len(limpo) >= 10 and limpo[2] == "/" and limpo[5] == "/":
        try:
            return datetime.strptime(limpo[:10], "%d/%m/%Y").date().toordinal()
        except ValueError:
            return None
    if len(limpo) >= 10 and limpo[4] == "-":
        try:
            return datetime.strptime(limpo[:10], "%Y-%m-%d").date().toordinal()
        except ValueError:
            return None
    return None


def _extrair_numero_ptbr(texto: str) -> float | None:
    limpo = texto.strip()
    if not limpo:
        return None

    if re.match(r"^[+-]?\d+([.,]\d+)?%$", limpo):
        bruto = limpo.rstrip("%").replace(".", "").replace(",", ".")
        try:
            return float(bruto)
        except ValueError:
            return None

    numeros = re.findall(r"[-+]?\d[\d.,]*", limpo.replace("R$", "").replace("US$", ""))
    if not numeros:
        return None

    bruto = numeros[0]
    if "," in bruto and "." in bruto:
        bruto = bruto.replace(".", "").replace(",", ".")
    elif "," in bruto:
        bruto = bruto.replace(",", ".")
    try:
        return float(bruto)
    except ValueError:
        return None
