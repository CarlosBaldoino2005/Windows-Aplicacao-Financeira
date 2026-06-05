"""Rotas de busca de acoes, cripto e FIIs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.dependencias import (
    obter_busca_cripto_servico,
    obter_busca_fiis_servico,
    obter_busca_servico,
)
from api.logica_mercado import normalizar_tipo_painel
from api.serializadores import busca_para_dict

router = APIRouter(prefix="/busca", tags=["Busca"])


def _montar_resposta_busca(
    termo: str,
    tipo: str,
    resultados: list,
    erro: str | None,
    limite: int,
) -> dict:
    lista = [busca_para_dict(item) for item in resultados[:limite]]
    return {
        "tipo": tipo,
        "termo": termo.strip(),
        "total": len(lista),
        "resultados": lista,
        "aviso": erro,
    }


def _executar_busca(tipo: str, termo: str, limite: int) -> tuple[list, str | None]:
    if tipo == "cripto":
        return obter_busca_cripto_servico().buscar(termo.strip(), limite=limite)
    if tipo == "fiis":
        return obter_busca_fiis_servico().buscar(termo.strip())
    return obter_busca_servico().buscar(termo.strip())


@router.get("/acoes")
def buscar_acoes(
    q: str = Query(..., min_length=1, description="Codigo ou nome"),
    limite: int = Query(default=12, ge=1, le=30),
    tipo: str = Query(default="acoes", description="acoes, cripto ou fiis"),
) -> dict:
    """Busca por termo conforme o tipo (local + Yahoo)."""
    tipo_ok = normalizar_tipo_painel(tipo)
    if tipo_ok == "indices":
        raise HTTPException(status_code=400, detail="Use o painel Indices para consultar indices.")

    resultados, erro = _executar_busca(tipo_ok, q, limite)
    if erro and not resultados:
        raise HTTPException(status_code=400, detail=erro)
    return _montar_resposta_busca(q, tipo_ok, resultados, erro, limite)


@router.get("/cripto")
def buscar_cripto(
    q: str = Query(..., min_length=1),
    limite: int = Query(default=12, ge=1, le=30),
) -> dict:
    """Alias de busca para criptomoedas."""
    return buscar_acoes(q=q, limite=limite, tipo="cripto")


@router.get("/fiis")
def buscar_fiis(
    q: str = Query(..., min_length=1),
    limite: int = Query(default=12, ge=1, le=30),
) -> dict:
    """Alias de busca para fundos imobiliarios."""
    return buscar_acoes(q=q, limite=limite, tipo="fiis")
