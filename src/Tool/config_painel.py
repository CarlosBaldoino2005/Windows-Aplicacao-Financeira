"""Leitura e gravacao da quantidade do painel em arquivo INI."""
from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

from src.Model.acoes_universo import QUANTIDADE_PADRAO_PAINEL
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import validar_quantidade_acoes

SECAO_PAINEL = "PAINEL"
CHAVE_QUANTIDADE = "quantidade_acoes"
NOME_ARQUIVO = "painel.ini"


class ConfigPainelIni:
    """Gerencia dados/painel.ini — um valor para alta, baixa e todas."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_dados = raiz / "dados"
        self._pasta_dados.mkdir(parents=True, exist_ok=True)
        self._caminho_ini = self._pasta_dados / NOME_ARQUIVO
        self._log = RegistradorLog(raiz)

    @property
    def caminho_arquivo(self) -> Path:
        return self._caminho_ini

    def padrao(self) -> int:
        return QUANTIDADE_PADRAO_PAINEL

    def carregar(self) -> int:
        """Le o INI; se nao existir, cria com valor padrao."""
        if not self._caminho_ini.exists():
            valor = self.padrao()
            self.salvar(valor)
            return valor

        parser = ConfigParser()
        try:
            parser.read(self._caminho_ini, encoding="utf-8")
        except Exception as exc:
            self._log.erro(f"Falha ao ler {NOME_ARQUIVO}: {exc}")
            return self.padrao()

        if SECAO_PAINEL not in parser:
            valor = self.padrao()
            self.salvar(valor)
            return valor

        secao = parser[SECAO_PAINEL]

        if CHAVE_QUANTIDADE in secao:
            return self._ler_valor(secao.get(CHAVE_QUANTIDADE))

        # Compatibilidade com INI antigo (tres chaves): usa quantidade_todas ou a primeira valida.
        for chave_antiga in (
            "quantidade_todas",
            "quantidade_em_alta",
            "quantidade_em_baixa",
        ):
            if chave_antiga in secao:
                valor = self._ler_valor(secao.get(chave_antiga))
                self.salvar(valor)
                return valor

        valor = self.padrao()
        self.salvar(valor)
        return valor

    def salvar(self, quantidade: int) -> None:
        parser = ConfigParser()
        parser[SECAO_PAINEL] = {CHAVE_QUANTIDADE: str(quantidade)}
        try:
            with open(self._caminho_ini, "w", encoding="utf-8") as arquivo:
                parser.write(arquivo)
        except OSError as exc:
            self._log.erro(f"Falha ao salvar {NOME_ARQUIVO}: {exc}")
            raise

    def _ler_valor(self, texto: str) -> int:
        valor, erro = validar_quantidade_acoes(texto)
        if erro or valor is None:
            return self.padrao()
        return valor
