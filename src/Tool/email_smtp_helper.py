"""Mensagens amigaveis e teste de conexao SMTP."""
from __future__ import annotations

import smtplib

from src.Model.opcoes_email_smtp import OpcoesSmtpEmail
from src.Tool.config_email import ConfigEmailIni


def traduzir_erro_smtp_amigavel(exc: Exception) -> str:
    """Converte erros tecnicos do SMTP em orientacao clara para o usuario."""
    texto = str(exc).lower()

    if "application-specific password" in texto or "invalidsecondfactor" in texto:
        return (
            "O Gmail exige senha de app (nao use a senha normal da conta). "
            "Em Google Conta > Seguranca > Verificacao em duas etapas > Senhas de app, "
            "gere uma senha de 16 caracteres e coloque em dados/email.ini (campo senha)."
        )

    if "basic authentication is disabled" in texto or "5.7.139" in texto:
        return (
            "O Outlook/Hotmail nao aceita a senha normal da conta neste tipo de envio. "
            "Ative verificacao em duas etapas em account.microsoft.com/security, "
            "crie uma senha de app e use essa senha em dados/email.ini. "
            "Alternativa mais simples: use Gmail com senha de app (smtp.gmail.com)."
        )

    if "username and password not accepted" in texto or "authentication failed" in texto:
        return (
            "Usuario ou senha SMTP recusados. Verifique dados/email.ini. "
            "No Gmail, use senha de app; no Outlook/Hotmail, confira usuario e senha."
        )

    if "connection unexpectedly closed" in texto or "timed out" in texto:
        return (
            "Nao foi possivel conectar ao servidor de e-mail. "
            "Confira servidor, porta e sua conexao com a internet."
        )

    if isinstance(exc, smtplib.SMTPException):
        return f"Falha ao enviar e-mail: {exc}"

    return f"Falha de conexao com o servidor de e-mail: {exc}"


def testar_conexao_smtp(opcoes: OpcoesSmtpEmail | None = None) -> tuple[bool, str | None]:
    """Testa login SMTP sem enviar mensagem. Retorna (ok, mensagem_erro)."""
    smtp = opcoes or ConfigEmailIni().carregar()
    if not smtp.configurado():
        return False, (
            "Servidor SMTP incompleto. Copie dados/email.example.ini para dados/email.ini "
            "e preencha servidor, usuario, senha e remetente."
        )

    try:
        if smtp.usar_tls:
            servidor = smtplib.SMTP(smtp.servidor, smtp.porta, timeout=30)
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()
        else:
            servidor = smtplib.SMTP_SSL(smtp.servidor, smtp.porta, timeout=30)

        servidor.login(smtp.usuario, smtp.senha)
        servidor.quit()
    except (smtplib.SMTPException, OSError) as exc:
        return False, traduzir_erro_smtp_amigavel(exc)

    return True, None
