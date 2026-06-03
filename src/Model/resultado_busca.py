"""Resultado da busca de acoes para adicionar na comparacao."""
from dataclasses import dataclass


@dataclass
class ResultadoBusca:
    simbolo: str
    nome: str
    bolsa: str
