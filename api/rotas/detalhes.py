"""Rotas de detalhes fundamentais de ativos."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.dependencias import (
    obter_detalhes_acao_servico,
    obter_detalhes_cripto_servico,
)
from api.serializadores import detalhes_para_dict
from src.Tool.fiis_helper import eh_fii
from src.Tool.validadores import normalizar_simbolo, normalizar_simbolo_cripto

router = APIRouter(prefix="/mercado", tags=["Detalhes"])


@router.get("/detalhes/{simbolo}")
def obter_detalhes(
    simbolo: str,
    tipo: str = Query(
        default="auto",
        description="auto, acao, fii ou cripto",
    ),
) -> dict:
    """Detalhes da empresa, FII ou criptomoeda (informacoes, indicadores, dividendos)."""
    tipo_norm = tipo.strip().lower()

    if tipo_norm in ("cripto", "crypto"):
        simbolo_ok, erro = normalizar_simbolo_cripto(simbolo)
        if erro:
            raise HTTPException(status_code=400, detail=erro)
        servico = obter_detalhes_cripto_servico()
        detalhes, erro_msg = servico.obter_detalhes(simbolo_ok)
    else:
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            raise HTTPException(status_code=400, detail=erro)
        if tipo_norm == "fii" and not eh_fii(simbolo_ok):
            raise HTTPException(status_code=400, detail="Codigo informado nao e um FII.")
        if tipo_norm == "auto" and simbolo_ok.endswith("-USD"):
            servico = obter_detalhes_cripto_servico()
            detalhes, erro_msg = servico.obter_detalhes(simbolo_ok)
            if detalhes:
                return {"detalhes": detalhes_para_dict(detalhes)}
        servico = obter_detalhes_acao_servico()
        detalhes, erro_msg = servico.obter_detalhes(simbolo_ok)

    if erro_msg and not detalhes:
        raise HTTPException(status_code=404, detail=erro_msg)
    if not detalhes:
        raise HTTPException(status_code=404, detail="Detalhes indisponiveis para este ativo.")

    return {"detalhes": detalhes_para_dict(detalhes)}
