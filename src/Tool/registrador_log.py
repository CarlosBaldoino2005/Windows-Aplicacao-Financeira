"""Grava logs diarios na pasta log conforme padrao global do projeto."""
from datetime import datetime
from pathlib import Path


class RegistradorLog:
    """Centraliza mensagens de log em arquivo diario."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        # Define a pasta raiz do projeto (tres niveis acima de src/Tool).
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_log = raiz / "log"
        self._pasta_log.mkdir(parents=True, exist_ok=True)
        nome_arquivo = f"log-{datetime.now().strftime('%d-%m-%Y')}.log"
        self._caminho_arquivo = self._pasta_log / nome_arquivo

    def _gravar(self, nivel: str, mensagem: str) -> None:
        # Monta linha com data/hora sem dados sensiveis na mensagem.
        linha = f"{datetime.now().isoformat(timespec='seconds')} [{nivel}] {mensagem}\n"
        with open(self._caminho_arquivo, "a", encoding="utf-8") as arquivo:
            arquivo.write(linha)

    def info(self, mensagem: str) -> None:
        self._gravar("INFO", mensagem)

    def aviso(self, mensagem: str) -> None:
        self._gravar("WARN", mensagem)

    def erro(self, mensagem: str) -> None:
        self._gravar("ERROR", mensagem)
