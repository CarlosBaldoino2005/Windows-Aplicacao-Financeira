"""Rotas de painel e cotacoes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.dependencias import obter_mercado_servico
from api.serializadores import cotacao_para_dict, lista_cotacoes_para_dict, serie_para_dict
from src.Model.acoes_universo import QUANTIDADE_MAXIMA_PAINEL, QUANTIDADE_PADRAO_PAINEL
from src.Tool.validadores import normalizar_simbolo

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
    servico = obter_mercado_servico()
    return {
        "quantidade": quantidade,
        "emAlta": lista_cotacoes_para_dict(servico.listar_em_alta(quantidade)),
        "emQueda": lista_cotacoes_para_dict(servico.listar_em_queda(quantidade)),
        "todas": lista_cotacoes_para_dict(servico.listar_todas_monitoradas(quantidade)),
    }


@router.get("/cotacao/{simbolo}")
def obter_cotacao(simbolo: str) -> dict:
    """Cotacao atual de uma acao pelo codigo (ex.: PETR4, AAPL)."""
    simbolo_ok, erro = normalizar_simbolo(simbolo)
    if erro:
        raise HTTPException(status_code=400, detail=erro)

    servico = obter_mercado_servico()
    resumos = servico.buscar_resumos([simbolo_ok])
    if not resumos:
        raise HTTPException(status_code=404, detail="Cotacao indisponivel. Verifique o codigo.")
    return {"cotacao": cotacao_para_dict(resumos[0])}


@router.get("/historico/{simbolo}")
def obter_historico(
    simbolo: str,
    periodo: str = Query(default="mes", description="dia, semana, mes, trimestre, semestre, ano"),
) -> dict:
    """Serie historica para graficos."""
    simbolo_ok, erro = normalizar_simbolo(simbolo)
    if erro:
        raise HTTPException(status_code=400, detail=erro)

    servico = obter_mercado_servico()
    serie = servico.buscar_historico(simbolo_ok, periodo)
    if not serie:
        raise HTTPException(status_code=404, detail="Historico indisponivel para este periodo.")
    return {"serie": serie_para_dict(serie)}
