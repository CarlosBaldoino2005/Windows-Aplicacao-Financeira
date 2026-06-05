"""Rotas de painel e cotacoes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.dependencias import obter_controlador_mercado
from api.serializadores import cotacao_para_dict, lista_cotacoes_para_dict, serie_para_dict
from src.Model.acoes_universo import QUANTIDADE_MAXIMA_PAINEL, QUANTIDADE_PADRAO_PAINEL

router = APIRouter(prefix="/mercado", tags=["Mercado"])


@router.get("/painel")
def obter_painel(
    quantidade: int = Query(
        default=QUANTIDADE_PADRAO_PAINEL,
        ge=1,
        le=QUANTIDADE_MAXIMA_PAINEL,
        description="Quantidade de acoes por aba",
    ),
) -> dict:
    """Painel Em alta, Em queda e Todas (mesma logica do desktop)."""
    controlador = obter_controlador_mercado()
    dados = controlador.obter_painel(quantidade)
    return {
        "quantidade": dados["quantidade"],
        "emAlta": lista_cotacoes_para_dict(dados["em_alta"]),
        "emQueda": lista_cotacoes_para_dict(dados["em_queda"]),
        "todas": lista_cotacoes_para_dict(dados["todas"]),
    }


@router.get("/cotacao/{simbolo}")
def obter_cotacao(simbolo: str) -> dict:
    """Cotacao atual de uma acao pelo codigo (ex.: PETR4, AAPL)."""
    controlador = obter_controlador_mercado()
    resumo, erro = controlador.obter_cotacao(simbolo)
    if erro:
        raise HTTPException(status_code=400, detail=erro)
    if resumo is None:
        raise HTTPException(status_code=404, detail="Cotacao nao encontrada.")
    return {"cotacao": cotacao_para_dict(resumo)}


@router.get("/historico/{simbolo}")
def obter_historico(
    simbolo: str,
    periodo: str = Query(default="mes", description="dia, semana, mes, trimestre, semestre, ano"),
) -> dict:
    """Serie historica para graficos (fase 2 do app; ja exposta na API)."""
    controlador = obter_controlador_mercado()
    serie, erro = controlador.obter_historico(simbolo, periodo)
    if erro:
        raise HTTPException(status_code=400, detail=erro)
    if serie is None:
        raise HTTPException(status_code=404, detail="Historico nao encontrado.")
    return {"serie": serie_para_dict(serie)}
