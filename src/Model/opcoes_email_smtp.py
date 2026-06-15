"""Opcoes de envio do relatorio PDF da carteira por e-mail."""
from __future__ import annotations

from dataclasses import dataclass

MAXIMO_EMAILS_RELATORIO = 20


@dataclass(frozen=True)
class OpcoesSmtpEmail:
    """Credenciais e servidor SMTP para envio de relatorios."""

    servidor: str
    porta: int
    usuario: str
    senha: str
    remetente: str
    usar_tls: bool

    def configurado(self) -> bool:
        return bool(
            self.servidor.strip()
            and self.usuario.strip()
            and self.senha.strip()
            and self.remetente.strip()
            and self.porta > 0
        )
