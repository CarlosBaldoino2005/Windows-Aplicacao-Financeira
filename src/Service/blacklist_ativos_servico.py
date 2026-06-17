"""Persistencia local da Black List de ativos que o usuario prefere evitar cadastrar."""
from __future__ import annotations

import json
from pathlib import Path

from src.Tool.carteira_ativo_helper import normalizar_simbolo_carteira
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import normalizar_simbolo, normalizar_simbolo_cripto

MAXIMO_BLACKLIST = 200
_ARQUIVO_NOME = "blacklist_ativos.json"


def normalizar_simbolo_blacklist(entrada: str) -> tuple[str | None, str | None]:
    """Normaliza codigo para gravacao e comparacao na Black List."""
    texto = (entrada or "").strip()
    if not texto:
        return None, "Informe o codigo do ativo."

    simbolo_carteira, _, erro_carteira = normalizar_simbolo_carteira(texto)
    if simbolo_carteira and not erro_carteira:
        return simbolo_carteira, None

    simbolo_acao, erro_acao = normalizar_simbolo(texto)
    if simbolo_acao and not erro_acao:
        return simbolo_acao, None

    simbolo_cripto, erro_cripto = normalizar_simbolo_cripto(texto)
    if simbolo_cripto and not erro_cripto:
        return simbolo_cripto, None

    return None, erro_carteira or erro_acao or erro_cripto or "Codigo invalido."


class BlacklistAtivosServico:
    """Grava e le simbolos da Black List em JSON na pasta dados do projeto."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_dados = raiz / "dados"
        self._pasta_dados.mkdir(parents=True, exist_ok=True)
        self._caminho_arquivo = self._pasta_dados / _ARQUIVO_NOME
        self._log = RegistradorLog(raiz)

    def listar(self) -> list[str]:
        """Retorna simbolos na ordem de inclusao."""
        dados = self._ler_arquivo()
        return list(dados.get("simbolos", []))

    def esta_na_lista(self, simbolo: str) -> bool:
        """Verifica se o simbolo (ou sua forma normalizada) esta na Black List."""
        simbolo_ok, erro = normalizar_simbolo_blacklist(simbolo)
        if erro or not simbolo_ok:
            return False
        return simbolo_ok in self.listar()

    def adicionar(self, simbolo: str) -> tuple[bool, str | None]:
        simbolo_ok, erro = normalizar_simbolo_blacklist(simbolo)
        if erro:
            return False, erro

        lista = self.listar()
        rotulo = self._rotulo_exibicao(simbolo_ok)
        if simbolo_ok in lista:
            return False, f"{rotulo} ja esta na Black List."

        if len(lista) >= MAXIMO_BLACKLIST:
            return False, f"Maximo de {MAXIMO_BLACKLIST} ativos na Black List."

        lista.append(simbolo_ok)
        self._salvar(lista)
        return True, None

    def remover(self, simbolo: str) -> tuple[bool, str | None]:
        simbolo_ok, erro = normalizar_simbolo_blacklist(simbolo)
        if erro:
            return False, erro

        lista = self.listar()
        if simbolo_ok not in lista:
            return False, "Ativo nao encontrado na Black List."

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
            self._log.erro(f"Falha ao ler Black List: {exc}")
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
            ok, _ = normalizar_simbolo_blacklist(item)
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
            self._log.erro(f"Falha ao salvar Black List: {exc}")
            raise
