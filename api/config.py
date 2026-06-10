"""Configuracao da API (variaveis de ambiente e CORS)."""
from __future__ import annotations

import os

VERSAO_API = "1.1.0"


def obter_porta() -> int:
    """Porta do servidor (padrao 8000 local; Docker pode injetar PORT)."""
    try:
        return int(os.getenv("PORT", "8000"))
    except ValueError:
        return 8000


def obter_chave_api() -> str:
    """Chave opcional; se vazia, a API aceita requisicoes sem autenticacao."""
    return os.getenv("FINANCEIRO_API_KEY", "").strip()


def origens_cors() -> list[str]:
    """Origens permitidas para testes no navegador; app Android nativo nao usa CORS."""
    extra = os.getenv("FINANCEIRO_CORS_ORIGENS", "").strip()
    if extra:
        return [o.strip() for o in extra.split(",") if o.strip()]
    return ["*"]
