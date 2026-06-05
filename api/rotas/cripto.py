"""Rotas de painel e cotacoes de criptomoedas (alias da rota unificada)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.logica_mercado import buscar_cotacao, buscar_historico, montar_painel
from api.serializadores import cotacao_para_dict, lista_cotacoes_para_dict, serie_para_dict
from src.Model.cripto_universo import QUANTIDADE_MAXIMA_CRIPTO, QUANTIDADE_PADRAO_CRIPTO
from src.Tool.validadores import normalizar_simbolo_cripto

router = APIRouter(prefix="/mercado/cripto", tags=["Criptomoedas"])


@router.get("/painel")
def obter_painel_cripto(
    quantidade: int = Query(
        default=QUANTIDADE_PADRAO_CRIPTO,
        ge=1,
        le=QUANTIDADE_MAXIMA_CRIPTO,
    ),
) -> dict:
    painel = montar_painel("cripto", quantidade)
    return {
        "tipo": "cripto",
        "quantidade": quantidade,
        "emAlta": lista_cotacoes_para_dict(painel["emAlta"]),
        "emQueda": lista_cotacoes_para_dict(painel["emQueda"]),
        "todas": lista_cotacoes_para_dict(painel["todas"]),
    }


@router.get("/cotacao/{simbolo}")
def obter_cotacao_cripto(simbolo: str) -> dict:
    simbolo_ok, erro = normalizar_simbolo_cripto(simbolo)
    if erro:
        raise HTTPException(status_code=400, detail=erro)
    try:
        resumo = buscar_cotacao("cripto", simbolo_ok)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not resumo:
        raise HTTPException(status_code=404, detail="Cotacao indisponivel. Verifique o codigo.")
    return {"tipo": "cripto", "cotacao": cotacao_para_dict(resumo)}


@router.get("/historico/{simbolo}")
def obter_historico_cripto(
    simbolo: str,
    periodo: str = Query(default="mes"),
) -> dict:
    simbolo_ok, erro = normalizar_simbolo_cripto(simbolo)
    if erro:
        raise HTTPException(status_code=400, detail=erro)
    serie = buscar_historico("cripto", simbolo_ok, periodo)
    if not serie:
        raise HTTPException(status_code=404, detail="Historico indisponivel para este periodo.")
    return {"tipo": "cripto", "serie": serie_para_dict(serie)}
