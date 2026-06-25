"""Leitura e gravacao da configuracao de IA (provedor e chave) no .env."""
from __future__ import annotations

import os
from dataclasses import dataclass

from src.Service.provedores.util_provedor import (
    aplicar_variaveis_ambiente,
    carregar_variaveis_ambiente,
    obter_caminho_env,
)
from src.Tool.registrador_log import RegistradorLog

_PROVEDORES = ("gemini", "groq", "openai")

_CHAVE_POR_PROVEDOR = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
}

_ROTULOS_PROVEDOR = {
    "gemini": "Google Gemini (gratuito)",
    "groq": "Groq (gratuito)",
    "openai": "OpenAI (pago)",
}

_URL_CHAVE = {
    "gemini": "https://aistudio.google.com/apikey",
    "groq": "https://console.groq.com",
    "openai": "https://platform.openai.com/api-keys",
}

_MODELO_PADRAO = {
    "gemini": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
}


@dataclass(frozen=True)
class ConfigAnaliseIa:
    """Configuracao atual da analise com IA."""

    provedor: str
    chave_api: str

    @property
    def configurada(self) -> bool:
        return bool(self.chave_api.strip())

    @property
    def rotulo_provedor(self) -> str:
        return _ROTULOS_PROVEDOR.get(self.provedor, self.provedor)


def listar_provedores_ia() -> tuple[tuple[str, str], ...]:
    """Retorna pares (id, rotulo) para exibir na tela."""
    return tuple((provedor, _ROTULOS_PROVEDOR[provedor]) for provedor in _PROVEDORES)


def url_chave_provedor(provedor: str) -> str:
    return _URL_CHAVE.get(provedor, "")


def _chave_ambiente_provedor(provedor: str) -> str:
    nome = _CHAVE_POR_PROVEDOR.get(provedor, "")
    return (os.getenv(nome, "") or "").strip() if nome else ""


def _normalizar_provedor(provedor: str) -> str | None:
    valor = (provedor or "").strip().lower()
    if valor in _PROVEDORES:
        return valor
    return None


def ler_config_analise_ia() -> ConfigAnaliseIa:
    """Le provedor e chave ativos (memoria ou .env)."""
    carregar_variaveis_ambiente()

    preferido = (os.getenv("IA_PROVEDOR", "auto") or "auto").strip().lower()
    if preferido != "auto":
        provedor = _normalizar_provedor(preferido)
        if provedor:
            return ConfigAnaliseIa(provedor=provedor, chave_api=_chave_ambiente_provedor(provedor))

    for provedor in _PROVEDORES:
        chave = _chave_ambiente_provedor(provedor)
        if chave:
            return ConfigAnaliseIa(provedor=provedor, chave_api=chave)

    return ConfigAnaliseIa(provedor="gemini", chave_api="")


def _mesclar_env(atualizacoes: dict[str, str]) -> None:
    caminho = obter_caminho_env()
    linhas_originais: list[str] = []
    if caminho.exists():
        try:
            linhas_originais = caminho.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise OSError("Nao foi possivel ler o arquivo .env.") from exc

    resultado: list[str] = []
    chaves_atualizadas: set[str] = set()

    for linha in linhas_originais:
        texto = linha.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            resultado.append(linha)
            continue
        chave, _ = linha.split("=", 1)
        chave = chave.strip()
        if chave in atualizacoes:
            resultado.append(f"{chave}={atualizacoes[chave]}")
            chaves_atualizadas.add(chave)
        else:
            resultado.append(linha)

    faltantes = [chave for chave in atualizacoes if chave not in chaves_atualizadas]
    if faltantes:
        if not linhas_originais:
            resultado.append("# Configuracao local (nao versionar)")
        elif resultado and resultado[-1].strip():
            resultado.append("")
        resultado.append("# Analise com IA (tela Agora)")
        for chave in faltantes:
            resultado.append(f"{chave}={atualizacoes[chave]}")

    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        texto_final = "\n".join(resultado).rstrip() + "\n"
        caminho.write_text(texto_final, encoding="utf-8")
    except OSError as exc:
        raise OSError("Nao foi possivel gravar o arquivo .env.") from exc


def salvar_config_analise_ia(provedor: str, chave_api: str) -> tuple[bool, str]:
    """
    Grava provedor e chave no .env e aplica em memoria.
    Retorna (sucesso, mensagem_erro).
    """
    provedor_norm = _normalizar_provedor(provedor)
    if provedor_norm is None:
        return False, "Selecione um provedor de IA valido."

    chave = (chave_api or "").strip()
    if not chave:
        atual = ler_config_analise_ia()
        if atual.provedor == provedor_norm and atual.chave_api:
            chave = atual.chave_api
        else:
            return False, "Informe a chave de API do provedor selecionado."

    chave_env = _CHAVE_POR_PROVEDOR[provedor_norm]
    modelo_env = {
        "gemini": "GEMINI_MODEL",
        "groq": "GROQ_MODEL",
        "openai": "OPENAI_MODEL",
    }[provedor_norm]

    atualizacoes = {
        "IA_PROVEDOR": provedor_norm,
        chave_env: chave,
        modelo_env: _MODELO_PADRAO[provedor_norm],
    }

    try:
        _mesclar_env(atualizacoes)
    except OSError as exc:
        return False, str(exc)

    aplicar_variaveis_ambiente(atualizacoes)
    RegistradorLog().info(f"Configuracao de IA salva (provedor={provedor_norm}).")
    return True, ""
