"""Persistencia local da lista de acoes favoritas do usuario."""
from __future__ import annotations

import json
from pathlib import Path

from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import normalizar_simbolo

MAXIMO_FAVORITOS = 40
_ARQUIVO_NOME = "favoritos.json"


class FavoritosServico:
    """Grava e le simbolos favoritos em JSON na pasta dados do projeto."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_dados = raiz / "dados"
        self._pasta_dados.mkdir(parents=True, exist_ok=True)
        self._caminho_arquivo = self._pasta_dados / _ARQUIVO_NOME
        self._log = RegistradorLog(raiz)

    def listar(self) -> list[str]:
        """Retorna tickers favoritos na ordem de inclusao."""
        dados = self._ler_arquivo()
        return list(dados.get("simbolos", []))

    def adicionar(self, simbolo: str) -> tuple[bool, str | None]:
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            return False, erro

        lista = self.listar()
        if simbolo_ok in lista:
            return False, f"{simbolo_ok.replace('.SA', '')} ja esta nos favoritos."

        if len(lista) >= MAXIMO_FAVORITOS:
            return False, f"Maximo de {MAXIMO_FAVORITOS} acoes favoritas."

        lista.append(simbolo_ok)
        self._salvar(lista)
        return True, None

    def remover(self, simbolo: str) -> tuple[bool, str | None]:
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            return False, erro

        lista = self.listar()
        if simbolo_ok not in lista:
            return False, "Acao nao encontrada nos favoritos."

        lista = [item for item in lista if item != simbolo_ok]
        self._salvar(lista)
        return True, None

    def _ler_arquivo(self) -> dict:
        if not self._caminho_arquivo.exists():
            return {"simbolos": []}

        try:
            with open(self._caminho_arquivo, encoding="utf-8") as arquivo:
                conteudo = json.load(arquivo)
        except (json.JSONDecodeError, OSError) as exc:
            self._log.erro(f"Falha ao ler favoritos: {exc}")
            return {"simbolos": []}

        if not isinstance(conteudo, dict):
            return {"simbolos": []}

        simbolos = conteudo.get("simbolos", [])
        if not isinstance(simbolos, list):
            return {"simbolos": []}

        validos: list[str] = []
        for item in simbolos:
            if not isinstance(item, str):
                continue
            ok, _ = normalizar_simbolo(item)
            if ok and ok not in validos:
                validos.append(ok)

        return {"simbolos": validos}

    def _salvar(self, simbolos: list[str]) -> None:
        payload = {"simbolos": simbolos}
        try:
            with open(self._caminho_arquivo, "w", encoding="utf-8") as arquivo:
                json.dump(payload, arquivo, ensure_ascii=False, indent=2)
        except OSError as exc:
            self._log.erro(f"Falha ao salvar favoritos: {exc}")
            raise
