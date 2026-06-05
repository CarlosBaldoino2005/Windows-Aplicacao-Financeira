"""Rotas de busca de acoes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.dependencias import obter_controlador_mercado
from api.serializadores import busca_para_dict

router = APIRouter(prefix="/busca", tags=["Busca"])


@router.get("/acoes")
def buscar_acoes(
    q: str = Query(..., min_length=1, description="Codigo ou nome da acao"),
    limite: int = Query(default=12, ge=1, le=30),
) -> dict:
    """Busca acoes por termo (local + Yahoo)."""
    controlador = obter_controlador_mercado()
    resultados, erro = controlador.pesquisar_acoes(q.strip())
    if erro and not resultados:
        raise HTTPException(status_code=400, detail=erro)

    lista = [busca_para_dict(item) for item in resultados[:limite]]
    return {
        "termo": q.strip(),
        "total": len(lista),
        "resultados": lista,
        "aviso": erro,
    }
