"""Execucao headless do relatorio agendado (servico Windows ou app aberta)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.opcoes_relatorio_automatico_carteira import OpcoesRelatorioAutomaticoCarteira
from src.Service.email_relatorio_servico import EmailRelatorioServico
from src.Service.relatorio_carteira_servico import RelatorioCarteiraServico
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.registrador_log import RegistradorLog

NOME_ARQUIVO_ESTADO = "relatorio_automatico_estado.json"
NOME_ARQUIVO_LOCK = "relatorio_automatico.lock"
INTERVALO_VERIFICACAO_SEGUNDOS = 30


@dataclass(frozen=True)
class ResultadoRelatorioAgendado:
    executado: bool
    mensagem: str | None = None
    caminho_pdf: Path | None = None


def _raiz_projeto() -> Path:
    return Path(__file__).resolve().parents[2]


def _caminho_estado() -> Path:
    pasta = _raiz_projeto() / "dados"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta / NOME_ARQUIVO_ESTADO


def _caminho_lock() -> Path:
    return _raiz_projeto() / "dados" / NOME_ARQUIVO_LOCK


def _carregar_estado() -> dict:
    caminho = _caminho_estado()
    if not caminho.is_file():
        return {"ultima_data": "", "slots_executados": []}
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return {"ultima_data": "", "slots_executados": []}
    if not isinstance(dados, dict):
        return {"ultima_data": "", "slots_executados": []}
    slots = dados.get("slots_executados")
    if not isinstance(slots, list):
        slots = []
    return {
        "ultima_data": str(dados.get("ultima_data") or ""),
        "slots_executados": [str(item) for item in slots],
    }


def _salvar_estado(estado: dict) -> None:
    caminho = _caminho_estado()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(estado, arquivo, ensure_ascii=False, indent=2)


def _chave_slot(agora: datetime, horario: str) -> str:
    return f"{agora.strftime('%d-%m-%Y')} {horario}"


def _horario_coincide(agora: datetime, horario: str) -> bool:
    partes = horario.split(":")
    if len(partes) != 2:
        return False
    try:
        hora = int(partes[0])
        minuto = int(partes[1])
    except ValueError:
        return False
    return agora.hour == hora and agora.minute == minuto


def _obter_horario_disparo(
    opcoes: OpcoesRelatorioAutomaticoCarteira,
    agora: datetime | None = None,
) -> str | None:
    momento = agora or datetime.now()
    if not opcoes.habilitado or not opcoes.horarios:
        return None
    for horario in opcoes.horarios:
        if _horario_coincide(momento, horario):
            return horario
    return None


class _LockExecucaoRelatorio:
    """Evita dois envios no mesmo minuto (app + servico Windows)."""

    def __init__(self) -> None:
        self._arquivo = None
        self._adquirido = False

    def __enter__(self):
        caminho = _caminho_lock()
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self._arquivo = open(caminho, "a+b")
        try:
            import msvcrt

            self._arquivo.seek(0)
            msvcrt.locking(self._arquivo.fileno(), msvcrt.LK_NBLCK, 1)
            self._adquirido = True
        except OSError:
            pass
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._arquivo is None:
            return
        try:
            if self._adquirido:
                import msvcrt

                self._arquivo.seek(0)
                msvcrt.locking(self._arquivo.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        try:
            self._arquivo.close()
        except OSError:
            pass

    @property
    def adquirido(self) -> bool:
        return self._adquirido


def _reservar_slot_execucao(horario: str, agora: datetime) -> bool:
    """Registra o horario do dia se ainda nao foi executado."""
    chave = _chave_slot(agora, horario)
    estado = _carregar_estado()
    hoje = agora.strftime("%d-%m-%Y")
    if estado.get("ultima_data") != hoje:
        estado = {"ultima_data": hoje, "slots_executados": []}
    if chave in estado["slots_executados"]:
        return False
    estado["slots_executados"].append(chave)
    _salvar_estado(estado)
    return True


def limpar_estado_agendamento_relatorio() -> None:
    """Usado ao salvar nova configuracao na carteira."""
    caminho = _caminho_estado()
    if caminho.is_file():
        try:
            caminho.unlink()
        except OSError:
            pass


def gerar_e_enviar_relatorio_carteira(
    *,
    abrir_pdf: bool = False,
    pasta_base: Path | None = None,
) -> ResultadoRelatorioAgendado:
    """Gera PDF e envia e-mail conforme destinatarios em painel.ini."""
    raiz = pasta_base or _raiz_projeto()
    log = RegistradorLog(raiz)
    controlador = ControladorCarteira()
    caminho, erro, assunto = controlador.gerar_relatorio_pdf()
    if erro or caminho is None:
        log.erro(f"Relatorio agendado: {erro or 'falha ao gerar PDF'}")
        return ResultadoRelatorioAgendado(False, erro or "Falha ao gerar PDF.")

    opcoes = controlador.carregar_relatorio_automatico()
    erro_email: str | None = None
    if opcoes.emails_destinatarios:
        _, erro_email = EmailRelatorioServico(raiz).enviar_relatorio_pdf(
            caminho,
            opcoes.emails_destinatarios,
            assunto=assunto or "",
        )

    if abrir_pdf:
        RelatorioCarteiraServico.abrir_pdf_no_sistema(caminho)

    if erro_email:
        log.erro(f"Relatorio agendado: PDF gerado, e-mail falhou.")
        return ResultadoRelatorioAgendado(
            True,
            f"PDF gerado, mas e-mail falhou: {erro_email}",
            caminho,
        )

    if opcoes.emails_destinatarios:
        log.info(
            f"Relatorio agendado: PDF gerado e e-mail enviado para "
            f"{len(opcoes.emails_destinatarios)} destinatario(s)."
        )
    else:
        log.info(f"Relatorio agendado: PDF gerado em {caminho.name}.")

    return ResultadoRelatorioAgendado(True, None, caminho)


def executar_ciclo_relatorio_agendado(
    *,
    abrir_pdf: bool = False,
    pasta_base: Path | None = None,
) -> ResultadoRelatorioAgendado:
    """
    Verifica painel.ini e dispara relatorio se estiver em um horario configurado.
    Retorna executado=False quando nao era hora ou relatorio automatico desligado.
    """
    raiz = pasta_base or _raiz_projeto()
    os.chdir(raiz)
    config = ConfigPainelIni(raiz)
    opcoes = config.carregar_relatorio_automatico_carteira()
    agora = datetime.now()
    horario = _obter_horario_disparo(opcoes, agora)
    if horario is None:
        return ResultadoRelatorioAgendado(False)

    with _LockExecucaoRelatorio() as lock:
        if not lock.adquirido:
            return ResultadoRelatorioAgendado(False, "Outra instancia ja esta executando.")
        if not _reservar_slot_execucao(horario, agora):
            return ResultadoRelatorioAgendado(False)

    return gerar_e_enviar_relatorio_carteira(abrir_pdf=abrir_pdf, pasta_base=raiz)
