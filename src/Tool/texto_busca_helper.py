"""Normalizacao de texto para buscas sem diferenciar maiusculas e acentos."""
from __future__ import annotations

import unicodedata


def normalizar_texto_busca(texto: str) -> str:
    """Converte para minusculas e remove acentos para comparacao de busca."""
    if not texto:
        return ""

    sem_acento = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caractere) != "Mn"
    )
    return sem_acento.strip()


def texto_contem_busca(termo: str, *textos: str) -> bool:
    """Verifica se o termo aparece em algum texto, ignorando caixa e acentos."""
    chave = normalizar_texto_busca(termo)
    if not chave:
        return False

    for texto in textos:
        if chave in normalizar_texto_busca(texto):
            return True
    return False
