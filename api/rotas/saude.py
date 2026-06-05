"""Rota de saude para monitoramento e deploy."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Saude"])


@router.get("/saude")
def verificar_saude() -> dict:
    """Confirma que a API esta no ar (usado pelo Render e pelo app)."""
    return {
        "status": "ok",
        "servico": "financeiro-api",
        "versao": "1.0.0",
    }
