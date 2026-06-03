"""Cores e modos claro/escuro do modelo-ui aplicados na interface Python."""
from __future__ import annotations

import json
from pathlib import Path

import customtkinter as ctk

MODOS_APARENCIA = ("claro", "escuro")
MODO_PADRAO = "claro"
_ROTULO_PARA_MODO = {"Claro": "claro", "Escuro": "escuro"}
_MODO_PARA_ROTULO = {"claro": "Claro", "escuro": "Escuro"}

_modo_atual: str = MODO_PADRAO
CORES: dict[str, str] = {}


def _caminho_tokens() -> Path:
    return Path(__file__).resolve().parents[2] / "modelo-ui" / "design-tokens.json"


def _ler_arquivo_tokens() -> dict:
    with open(_caminho_tokens(), encoding="utf-8") as arquivo:
        return json.load(arquivo)


def normalizar_modo_aparencia(texto: str) -> str:
    """Aceita claro, escuro, light, dark (case insensitive)."""
    if not texto or not str(texto).strip():
        return MODO_PADRAO
    limpo = str(texto).strip().lower()
    if limpo in ("escuro", "dark", "noite"):
        return "escuro"
    return "claro"


def carregar_paleta(modo: str) -> dict[str, str]:
    dados = _ler_arquivo_tokens()
    modo_norm = normalizar_modo_aparencia(modo)
    modos = dados.get("modos") or {}
    if modo_norm in modos:
        return dict(modos[modo_norm])
    return dict(dados.get("cores") or {})


def aplicar_modo_aparencia(modo: str) -> str:
    """Define CustomTkinter e o dicionario CORES usado em toda a interface."""
    global _modo_atual
    modo_norm = normalizar_modo_aparencia(modo)
    _modo_atual = modo_norm
    ctk.set_appearance_mode("dark" if modo_norm == "escuro" else "light")
    ctk.set_default_color_theme("blue")
    CORES.clear()
    CORES.update(carregar_paleta(modo_norm))
    return modo_norm


def obter_modo_aparencia() -> str:
    return _modo_atual


def rotulo_modo_aparencia(modo: str | None = None) -> str:
    return _MODO_PARA_ROTULO.get(normalizar_modo_aparencia(modo or _modo_atual), "Claro")


def modo_de_rotulo(rotulo: str) -> str:
    return _ROTULO_PARA_MODO.get(rotulo, MODO_PADRAO)


aplicar_modo_aparencia(MODO_PADRAO)
