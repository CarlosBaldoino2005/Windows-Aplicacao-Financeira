"""Timer reutilizavel para atualizar cotacoes conforme dados/painel.ini."""
from __future__ import annotations

import weakref
from collections.abc import Callable
from typing import Literal

from src.Model.opcoes_atualizacao_automatica import OpcoesAtualizacaoAutomatica
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import janela_ui_ainda_ativa

EscopoAtualizacaoAutomatica = Literal["painel", "monitoramento", "carteira"]

_registrados_painel: list[weakref.ReferenceType["GerenciadorAtualizacaoAutomatica"]] = []
_registrados_monitoramento: list[weakref.ReferenceType["GerenciadorAtualizacaoAutomatica"]] = []
_registrados_carteira: list[weakref.ReferenceType["GerenciadorAtualizacaoAutomatica"]] = []


def _lista_por_escopo(escopo: EscopoAtualizacaoAutomatica):
    if escopo == "monitoramento":
        return _registrados_monitoramento
    if escopo == "carteira":
        return _registrados_carteira
    return _registrados_painel


def _reagendar_registrados(registrados: list) -> None:
    vivos: list = []
    for referencia in registrados:
        gerenciador = referencia()
        if gerenciador is None:
            continue
        vivos.append(referencia)
        gerenciador.reagendar()
    registrados.clear()
    registrados.extend(vivos)


def notificar_mudanca_configuracao_atualizacao_automatica() -> None:
    """Reagenda paineis de cotacoes apos salvar configuracao global."""
    _reagendar_registrados(_registrados_painel)


def notificar_mudanca_configuracao_atualizacao_automatica_monitoramento() -> None:
    """Reagenda a tela de monitoramento apos salvar sua configuracao."""
    _reagendar_registrados(_registrados_monitoramento)


def notificar_mudanca_configuracao_atualizacao_automatica_carteira() -> None:
    """Reagenda a tela de carteira apos salvar sua configuracao."""
    _reagendar_registrados(_registrados_carteira)


class GerenciadorAtualizacaoAutomatica:
    """Dispara callback periodicamente enquanto a janela existir e a opcao estiver ativa."""

    def __init__(
        self,
        janela,
        config: ConfigPainelIni | None,
        ao_atualizar: Callable[[], None],
        *,
        escopo: EscopoAtualizacaoAutomatica = "painel",
        carregar_opcoes: Callable[[], OpcoesAtualizacaoAutomatica] | None = None,
    ) -> None:
        self._janela = janela
        self._config = config or ConfigPainelIni()
        self._ao_atualizar = ao_atualizar
        self._escopo = escopo
        self._job_id: str | None = None
        self._pausado_manual = False
        self._referencia = weakref.ref(self)
        self._lista_registro = _lista_por_escopo(escopo)
        if carregar_opcoes is not None:
            self._carregar_opcoes = carregar_opcoes
        elif escopo == "monitoramento":
            self._carregar_opcoes = self._config.carregar_atualizacao_automatica_monitoramento
        elif escopo == "carteira":
            self._carregar_opcoes = self._config.carregar_atualizacao_automatica_carteira
        else:
            self._carregar_opcoes = self._config.carregar_atualizacao_automatica
        self._lista_registro.append(self._referencia)

    def iniciar(self) -> None:
        self.reagendar()

    def parar(self) -> None:
        self._cancelar_timer()
        try:
            self._lista_registro.remove(self._referencia)
        except ValueError:
            pass

    def pausar(self) -> None:
        """Interrompe temporariamente o timer sem descadastrar o gerenciador."""
        self._pausado_manual = True
        self._cancelar_timer()

    def retomar(self) -> None:
        """Volta a agendar atualizacoes automaticas."""
        self._pausado_manual = False
        self.reagendar()

    def esta_pausado(self) -> bool:
        return self._pausado_manual

    def reagendar(self) -> None:
        self._cancelar_timer()
        if self._pausado_manual:
            return
        if not janela_ui_ainda_ativa(self._janela):
            return
        opcoes = self._carregar_opcoes()
        if not opcoes.habilitada:
            return
        atraso_ms = max(1, opcoes.intervalo_segundos) * 1000
        self._job_id = self._janela.after(atraso_ms, self._disparar)

    def obter_opcoes(self) -> OpcoesAtualizacaoAutomatica:
        return self._carregar_opcoes()

    def _cancelar_timer(self) -> None:
        if self._job_id is None:
            return
        try:
            self._janela.after_cancel(self._job_id)
        except Exception:
            pass
        self._job_id = None

    def _disparar(self) -> None:
        self._job_id = None
        if not janela_ui_ainda_ativa(self._janela):
            return
        try:
            self._ao_atualizar()
        finally:
            self.reagendar()
