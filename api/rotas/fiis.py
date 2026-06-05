"""Rotas de painel e cotacoes de fundos imobiliarios (alias da rota unificada)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.logica_mercado import buscar_cotacao, buscar_historico, montar_painel
from api.serializadores import cotacao_para_dict, lista_cotacoes_para_dict, serie_para_dict
from src.Model.fiis_universo import QUANTIDADE_MAXIMA_FIIS, QUANTIDADE_PADRAO_FIIS
from src.Tool.fiis_helper import eh_fii
from src.Tool.validadores import normalizar_simbolo

router = APIRouter(prefix="/mercado/fiis", tags=["Fundos Imobiliarios"])


@router.get("/painel")
def obter_painel_fiis(
    quantidade: int = Query(
        default=QUANTIDADE_PADRAO_FIIS,
        ge=1,
        le=QUANTIDADE_MAXIMA_FIIS,
    ),
) -> dict:
    painel = montar_painel("fiis", quantidade)
    return {
        "tipo": "fiis",
        "quantidade": quantidade,
        "emAlta": lista_cotacoes_para_dict(painel["emAlta"]),
        "emQueda": lista_cotacoes_para_dict(painel["emQueda"]),
        "todas": lista_cotacoes_para_dict(painel["todas"]),
    }


@router.get("/cotacao/{simbolo}")
def obter_cotacao_fii(simbolo: str) -> dict:
    simbolo_ok, erro = normalizar_simbolo(simbolo)
    if erro:
        raise HTTPException(status_code=400, detail=erro)
    if not eh_fii(simbolo_ok):
        raise HTTPException(status_code=400, detail="Codigo informado nao e um fundo imobiliario (FII).")
    try:
        resumo = buscar_cotacao("fiis", simbolo_ok)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not resumo:
        raise HTTPException(status_code=404, detail="Cotacao indisponivel. Verifique o codigo.")
    return {"tipo": "fiis", "cotacao": cotacao_para_dict(resumo)}


@router.get("/historico/{simbolo}")
def obter_historico_fii(
    simbolo: str,
    periodo: str = Query(default="mes"),
) -> dict:
    simbolo_ok, erro = normalizar_simbolo(simbolo)
    if erro:
        raise HTTPException(status_code=400, detail=erro)
    if not eh_fii(simbolo_ok):
        raise HTTPException(status_code=400, detail="Codigo informado nao e um fundo imobiliario (FII).")
    serie = buscar_historico("fiis", simbolo_ok, periodo)
    if not serie:
        raise HTTPException(status_code=404, detail="Historico indisponivel para este periodo.")
    return {"tipo": "fiis", "serie": serie_para_dict(serie)}
