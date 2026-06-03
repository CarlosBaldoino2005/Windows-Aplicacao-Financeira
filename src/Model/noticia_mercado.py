"""Noticia de mercado exibida na tela de noticias."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NoticiaMercado:
    """Resumo de uma noticia obtida via Yahoo Finance."""

    id: str
    titulo: str
    resumo: str
    data_publicacao: datetime | None
    data_exibicao: str
    fonte: str
    url: str
    regiao: str
    referencia: str = ""
    url_imagem: str = ""
