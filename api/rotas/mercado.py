"""Rotas de painel e cotacoes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.logica_mercado import (
    buscar_cotacao,
    buscar_historico,
    limites_quantidade,
    montar_painel,
    normalizar_tipo_painel,
)
from api.serializadores import cotacao_para_dict, lista_cotacoes_para_dict, serie_para_dict

router = APIRouter(prefix="/mercado", tags=["Mercado"])


@router.get("/painel")
def obter_painel(
    quantidade: int | None = Query(
        default=None,
        ge=1,
        description="Quantidade de ativos por aba",
    ),
    tipo: str = Query(
        default="acoes",
        description="acoes, cripto, fiis ou indices",
    ),
) -> dict:
    """Painel Em alta, Em queda e Todas (acoes, cripto, FIIs ou indices)."""
    tipo_ok = normalizar_tipo_painel(tipo)
    padrao, maximo = limites_quantidade(tipo_ok)
    qtd = quantidade if quantidade is not None else padrao
    if qtd > maximo:
        qtd = maximo

    painel = montar_painel(tipo_ok, qtd)
    return {
        "tipo": tipo_ok,
        "quantidade": qtd,
        "emAlta": lista_cotacoes_para_dict(painel["emAlta"]),
        "emQueda": lista_cotacoes_para_dict(painel["emQueda"]),
        "todas": lista_cotacoes_para_dict(painel["todas"]),
    }


@router.get("/cotacao/{simbolo}")
def obter_cotacao(
    simbolo: str,
    tipo: str = Query(default="acoes", description="acoes, cripto, fiis ou indices"),
) -> dict:
    """Cotacao atual pelo codigo e tipo de ativo."""
    tipo_ok = normalizar_tipo_painel(tipo)
    try:
        resumo = buscar_cotacao(tipo_ok, simbolo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not resumo:
        raise HTTPException(status_code=404, detail="Cotacao indisponivel. Verifique o codigo.")
    return {"tipo": tipo_ok, "cotacao": cotacao_para_dict(resumo)}


@router.get("/historico/{simbolo}")
def obter_historico(
    simbolo: str,
    periodo: str = Query(default="mes", description="dia, semana, mes, trimestre, semestre, ano"),
    tipo: str = Query(default="acoes", description="acoes, cripto, fiis ou indices"),
) -> dict:
    """Serie historica para graficos."""
    tipo_ok = normalizar_tipo_painel(tipo)
    try:
        serie = buscar_historico(tipo_ok, simbolo, periodo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not serie:
        raise HTTPException(status_code=404, detail="Historico indisponivel para este periodo.")
    return {"tipo": tipo_ok, "serie": serie_para_dict(serie)}
