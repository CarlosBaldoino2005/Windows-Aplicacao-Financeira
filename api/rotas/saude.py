"""Rota de saude para monitoramento e deploy."""
from __future__ import annotations

from fastapi import APIRouter

from api.config import VERSAO_API

router = APIRouter(tags=["Saude"])


@router.get("/saude")
def verificar_saude() -> dict:
    """Confirma que a API local esta no ar (app mobile e testes)."""
    return {
        "status": "ok",
        "servico": "financeiro-api",
        "versao": VERSAO_API,
        "recursos": [
            "painel-acoes",
            "painel-cripto",
            "painel-fiis",
            "painel-indices",
            "detalhes",
            "historico",
            "busca-cripto",
            "busca-fiis",
        ],
    }
