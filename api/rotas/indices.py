"""Rotas de indices de mercado (alias da rota unificada)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.logica_mercado import buscar_cotacao, buscar_historico, montar_painel
from api.serializadores import cotacao_para_dict, lista_cotacoes_para_dict, serie_para_dict
from src.Model.indices_universo import QUANTIDADE_MAXIMA_INDICES, QUANTIDADE_PADRAO_INDICES

router = APIRouter(prefix="/mercado/indices", tags=["Indices"])


@router.get("/painel")
def obter_painel_indices(
    quantidade: int = Query(
        default=QUANTIDADE_PADRAO_INDICES,
        ge=1,
        le=QUANTIDADE_MAXIMA_INDICES,
    ),
) -> dict:
    painel = montar_painel("indices", quantidade)
    return {
        "tipo": "indices",
        "quantidade": quantidade,
        "emAlta": lista_cotacoes_para_dict(painel["emAlta"]),
        "emQueda": lista_cotacoes_para_dict(painel["emQueda"]),
        "todas": lista_cotacoes_para_dict(painel["todas"]),
    }


@router.get("/cotacao/{simbolo}")
def obter_cotacao_indice(simbolo: str) -> dict:
    try:
        resumo = buscar_cotacao("indices", simbolo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not resumo:
        raise HTTPException(status_code=404, detail="Cotacao indisponivel para este indice.")
    return {"tipo": "indices", "cotacao": cotacao_para_dict(resumo)}


@router.get("/historico/{simbolo}")
def obter_historico_indice(
    simbolo: str,
    periodo: str = Query(default="mes"),
) -> dict:
    try:
        serie = buscar_historico("indices", simbolo, periodo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not serie:
        raise HTTPException(status_code=404, detail="Historico indisponivel para este periodo.")
    return {"tipo": "indices", "serie": serie_para_dict(serie)}
