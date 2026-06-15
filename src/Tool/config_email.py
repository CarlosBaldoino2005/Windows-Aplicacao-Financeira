"""Leitura da configuracao SMTP em dados/email.ini."""
from __future__ import annotations

import os
from configparser import ConfigParser
from pathlib import Path

from src.Model.opcoes_email_smtp import OpcoesSmtpEmail
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import validar_sim_nao_config

SECAO_SMTP = "SMTP"
CHAVE_SERVIDOR = "servidor"
CHAVE_PORTA = "porta"
CHAVE_USUARIO = "usuario"
CHAVE_SENHA = "senha"
CHAVE_REMETENTE = "remetente"
CHAVE_USAR_TLS = "usar_tls"
NOME_ARQUIVO = "email.ini"
VARIAVEL_SENHA_AMBIENTE = "SMTP_SENHA"


class ConfigEmailIni:
    """Gerencia dados/email.ini para envio de relatorios por e-mail."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_dados = raiz / "dados"
        self._pasta_dados.mkdir(parents=True, exist_ok=True)
        self._caminho_ini = self._pasta_dados / NOME_ARQUIVO
        self._log = RegistradorLog(raiz)

    @property
    def caminho_arquivo(self) -> Path:
        return self._caminho_ini

    def carregar(self) -> OpcoesSmtpEmail:
        if not self._caminho_ini.exists():
            return OpcoesSmtpEmail(
                servidor="",
                porta=587,
                usuario="",
                senha="",
                remetente="",
                usar_tls=True,
            )

        parser = self._ler_parser()
        if SECAO_SMTP not in parser:
            return OpcoesSmtpEmail("", 587, "", "", "", True)

        secao = parser[SECAO_SMTP]
        porta = self._ler_porta(secao.get(CHAVE_PORTA, "587"))
        usar_tls, _ = validar_sim_nao_config(secao.get(CHAVE_USAR_TLS, "sim"), padrao=True)
        senha_arquivo = (secao.get(CHAVE_SENHA) or "").strip()
        senha_ambiente = (os.environ.get(VARIAVEL_SENHA_AMBIENTE) or "").strip()
        senha = senha_ambiente or senha_arquivo

        return OpcoesSmtpEmail(
            servidor=(secao.get(CHAVE_SERVIDOR) or "").strip(),
            porta=porta,
            usuario=(secao.get(CHAVE_USUARIO) or "").strip(),
            senha=senha,
            remetente=(secao.get(CHAVE_REMETENTE) or "").strip(),
            usar_tls=usar_tls,
        )

    def _ler_parser(self) -> ConfigParser:
        parser = ConfigParser()
        try:
            parser.read(self._caminho_ini, encoding="utf-8")
        except Exception as exc:
            self._log.erro(f"Falha ao ler {NOME_ARQUIVO}: {exc}")
        return parser

    @staticmethod
    def _ler_porta(texto: str) -> int:
        try:
            porta = int(str(texto or "").strip())
        except ValueError:
            return 587
        if porta < 1 or porta > 65535:
            return 587
        return porta
