"""Persistencia local da lista de acoes favoritas do usuario."""
from __future__ import annotations

import json
from pathlib import Path

from src.Tool.registrador_log import RegistradorLog
from collections.abc import Callable

from src.Tool.validadores import normalizar_simbolo

MAXIMO_FAVORITOS = 40
_ARQUIVO_NOME = "favoritos.json"


class FavoritosServico:
    """Grava e le simbolos favoritos em JSON na pasta dados do projeto."""

    def __init__(
        self,
        pasta_base: Path | None = None,
        *,
        nome_arquivo: str = _ARQUIVO_NOME,
        fn_normalizar: Callable[[str], tuple[str | None, str | None]] | None = None,
        rotulo_ativo: str = "acao",
        maximo: int = MAXIMO_FAVORITOS,
    ) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_dados = raiz / "dados"
        self._pasta_dados.mkdir(parents=True, exist_ok=True)
        self._caminho_arquivo = self._pasta_dados / nome_arquivo
        self._log = RegistradorLog(raiz)
        self._fn_normalizar = fn_normalizar or normalizar_simbolo
        self._rotulo = rotulo_ativo
        self._maximo = maximo

    def listar(self) -> list[str]:
        """Retorna tickers favoritos na ordem de inclusao."""
        dados = self._ler_arquivo()
        return list(dados.get("simbolos", []))

    def adicionar(self, simbolo: str) -> tuple[bool, str | None]:
        simbolo_ok, erro = self._fn_normalizar(simbolo)
        if erro:
            return False, erro

        lista = self.listar()
        rotulo = self._rotulo_exibicao(simbolo_ok)
        if simbolo_ok in lista:
            return False, f"{rotulo} ja esta nos favoritos."

        if len(lista) >= self._maximo:
            return False, f"Maximo de {self._maximo} {self._rotulo}s favoritas."

        lista.append(simbolo_ok)
        self._salvar(lista)
        return True, None

    def remover(self, simbolo: str) -> tuple[bool, str | None]:
        simbolo_ok, erro = self._fn_normalizar(simbolo)
        if erro:
            return False, erro

        lista = self.listar()
        if simbolo_ok not in lista:
            return False, f"{self._rotulo.capitalize()} nao encontrada nos favoritos."

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
            ok, _ = self._fn_normalizar(item)
            if ok and ok not in validos:
                validos.append(ok)

        return {"simbolos": validos}

    @staticmethod
    def _rotulo_exibicao(simbolo: str) -> str:
        return simbolo.replace(".SA", "").replace("-USD", "")

    def _salvar(self, simbolos: list[str]) -> None:
        payload = {"simbolos": simbolos}
        try:
            with open(self._caminho_arquivo, "w", encoding="utf-8") as arquivo:
                json.dump(payload, arquivo, ensure_ascii=False, indent=2)
        except OSError as exc:
            self._log.erro(f"Falha ao salvar favoritos: {exc}")
            raise
