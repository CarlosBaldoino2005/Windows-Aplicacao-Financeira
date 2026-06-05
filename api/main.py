"""
API Financeiro — ponto de entrada FastAPI para o app Android.

Executar localmente:
  set PYTHONPATH=<raiz do projeto>
  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import VERSAO_API, obter_chave_api, origens_cors
from api.rotas import busca, cripto, detalhes, fiis, indices, mercado, saude


@asynccontextmanager
async def ciclo_vida(_app: FastAPI):
    """Inicializacao leve ao subir o servidor."""
    yield


app = FastAPI(
    title="Financeiro API",
    description="API do painel de mercado para o app Android Financeiro.",
    version=VERSAO_API,
    lifespan=ciclo_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_cors(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def validar_chave_api(request: Request, call_next):
    """Exige X-API-Key apenas quando FINANCEIRO_API_KEY estiver configurada."""
    chave_esperada = obter_chave_api()
    if chave_esperada and request.url.path not in ("/api/saude", "/docs", "/openapi.json", "/redoc"):
        chave_recebida = request.headers.get("X-API-Key", "")
        if chave_recebida != chave_esperada:
            return JSONResponse(status_code=401, content={"detail": "Chave de API invalida."})
    return await call_next(request)


app.include_router(saude.router, prefix="/api")
app.include_router(mercado.router, prefix="/api")
app.include_router(cripto.router, prefix="/api")
app.include_router(fiis.router, prefix="/api")
app.include_router(indices.router, prefix="/api")
app.include_router(detalhes.router, prefix="/api")
app.include_router(busca.router, prefix="/api")


@app.get("/")
def raiz() -> dict:
    return {
        "mensagem": "Financeiro API ativa.",
        "documentacao": "/docs",
        "saude": "/api/saude",
    }
