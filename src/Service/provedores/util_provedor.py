"""Utilitarios HTTP e conversao de simbolos entre provedores de mercado."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from src.Tool.registrador_log import RegistradorLog

_carregou_env = False


def carregar_variaveis_ambiente() -> None:
    """Le .env na raiz do projeto (opcional, sem dependencia extra)."""
    global _carregou_env
    if _carregou_env:
        return
    _carregou_env = True

    caminho = Path(__file__).resolve().parents[3] / ".env"
    if not caminho.exists():
        return

    try:
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            texto = linha.strip()
            if not texto or texto.startswith("#") or "=" not in texto:
                continue
            chave, valor = texto.split("=", 1)
            chave = chave.strip()
            valor = valor.strip().strip('"').strip("'")
            if chave and chave not in os.environ:
                os.environ[chave] = valor
    except OSError:
        pass


carregar_variaveis_ambiente()

TIMEOUT_SEGUNDOS = 20
USER_AGENT = "Financeiro-Desktop/1.0"


def obter_token_brapi() -> str | None:
    """Token opcional (mais limite de requisicoes na Brapi)."""
    token = os.getenv("BRAPI_TOKEN", "").strip()
    return token or None


def obter_chave_alpha_vantage() -> str | None:
    """Chave opcional Alpha Vantage (reforco para acoes EUA)."""
    chave = os.getenv("ALPHAVANTAGE_API_KEY", "").strip()
    return chave or None


def eh_acao_b3(simbolo: str) -> bool:
    return simbolo.upper().endswith(".SA")


def codigo_brapi(simbolo: str) -> str:
    return simbolo.upper().replace(".SA", "")


def requisicao_json(url: str, log: RegistradorLog | None = None) -> dict | list | None:
    """GET JSON com timeout; retorna None se falhar."""
    cabecalhos = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    token_brapi = obter_token_brapi()
    if token_brapi and "brapi.dev" in url:
        cabecalhos["Authorization"] = f"Bearer {token_brapi}"

    requisicao = urllib.request.Request(url, headers=cabecalhos)
    try:
        with urllib.request.urlopen(requisicao, timeout=TIMEOUT_SEGUNDOS) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as exc:
        if log:
            log.aviso(f"Falha HTTP em provedor: {exc}")
        return None


def timestamp_para_data(valor: int | float) -> datetime:
    return datetime.fromtimestamp(int(valor))


def data_para_exibicao(data: datetime) -> str:
    return data.strftime("%d/%m/%Y %H:%M") if (data.hour or data.minute) else data.strftime("%d/%m/%Y")
