"""Envio do relatorio PDF da carteira por e-mail (SMTP)."""
from __future__ import annotations

import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.Tool.config_email import ConfigEmailIni
from src.Tool.email_smtp_helper import traduzir_erro_smtp_amigavel
from src.Tool.registrador_log import RegistradorLog


class EmailRelatorioServico:
    """Anexa o PDF gerado e envia aos destinatarios configurados na carteira."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._config = ConfigEmailIni(raiz)
        self._log = RegistradorLog(raiz)

    def enviar_relatorio_pdf(
        self,
        caminho_pdf: Path,
        destinatarios: tuple[str, ...],
    ) -> tuple[bool, str | None]:
        if not destinatarios:
            return False, "Nenhum destinatario informado."

        caminho = Path(caminho_pdf)
        if not caminho.is_file():
            return False, "Arquivo PDF do relatorio nao encontrado."

        opcoes = self._config.carregar()
        if not opcoes.configurado():
            return False, (
                "Servidor SMTP nao configurado. Copie dados/email.example.ini "
                "para dados/email.ini e preencha servidor, usuario, senha e remetente."
            )

        try:
            conteudo_pdf = caminho.read_bytes()
        except OSError as exc:
            return False, f"Nao foi possivel ler o PDF: {exc}"

        assunto = f"Relatorio da carteira — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        corpo = (
            "Segue em anexo o relatorio automatico da sua carteira de investimentos.\n\n"
            "Gerado pelo aplicativo Financeiro."
        )

        mensagem = MIMEMultipart()
        mensagem["Subject"] = assunto
        mensagem["From"] = opcoes.remetente
        mensagem["To"] = ", ".join(destinatarios)
        mensagem.attach(MIMEText(corpo, "plain", "utf-8"))

        anexo = MIMEApplication(conteudo_pdf, _subtype="pdf")
        anexo.add_header("Content-Disposition", "attachment", filename=caminho.name)
        mensagem.attach(anexo)

        try:
            if opcoes.usar_tls:
                servidor = smtplib.SMTP(opcoes.servidor, opcoes.porta, timeout=60)
                servidor.ehlo()
                servidor.starttls()
                servidor.ehlo()
            else:
                servidor = smtplib.SMTP_SSL(opcoes.servidor, opcoes.porta, timeout=60)

            servidor.login(opcoes.usuario, opcoes.senha)
            servidor.sendmail(opcoes.remetente, list(destinatarios), mensagem.as_string())
            servidor.quit()
        except smtplib.SMTPException as exc:
            mensagem = traduzir_erro_smtp_amigavel(exc)
            self._log.erro(f"Falha SMTP ao enviar relatorio: {type(exc).__name__}")
            return False, mensagem
        except OSError as exc:
            mensagem = traduzir_erro_smtp_amigavel(exc)
            self._log.erro(f"Falha de rede ao enviar relatorio: {type(exc).__name__}")
            return False, mensagem

        self._log.info(
            f"Relatorio da carteira enviado por e-mail para {len(destinatarios)} destinatario(s)."
        )
        return True, None
