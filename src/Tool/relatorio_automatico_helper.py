"""Agendador de relatorio PDF da carteira por horarios fixos (HH:MM)."""
from __future__ import annotations

import weakref
from collections.abc import Callable
from datetime import date, datetime

from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import janela_ui_ainda_ativa

_registrados: list[weakref.ReferenceType["GerenciadorRelatorioAutomaticoCarteira"]] = []


def notificar_mudanca_configuracao_relatorio_automatico_carteira() -> None:
    """Reinicia o agendador apos salvar horarios na configuracao da carteira."""
    vivos: list = []
    for referencia in _registrados:
        gerenciador = referencia()
        if gerenciador is None:
            continue
        vivos.append(referencia)
        gerenciador.reagendar()
    _registrados.clear()
    _registrados.extend(vivos)


class GerenciadorRelatorioAutomaticoCarteira:
    """Verifica periodicamente se algum horario configurado deve disparar o PDF."""

    INTERVALO_VERIFICACAO_MS = 30_000

    def __init__(
        self,
        janela,
        ao_gerar: Callable[[], None],
        config: ConfigPainelIni | None = None,
    ) -> None:
        self._janela = janela
        self._ao_gerar = ao_gerar
        self._config = config or ConfigPainelIni()
        self._job_id: str | None = None
        self._slots_executados_hoje: set[str] = set()
        self._data_executada: date | None = None
        self._referencia = weakref.ref(self)
        _registrados.append(self._referencia)

    def iniciar(self) -> None:
        self._agendar_verificacao()

    def parar(self) -> None:
        self._cancelar_timer()
        try:
            _registrados.remove(self._referencia)
        except ValueError:
            pass

    def reagendar(self) -> None:
        """Limpa slots do dia ao mudar configuracao (evita confusao apos editar horarios)."""
        self._slots_executados_hoje.clear()
        self._data_executada = None

    def _cancelar_timer(self) -> None:
        if self._job_id is None:
            return
        try:
            self._janela.after_cancel(self._job_id)
        except Exception:
            pass
        self._job_id = None

    def _agendar_verificacao(self) -> None:
        if not janela_ui_ainda_ativa(self._janela):
            return
        self._job_id = self._janela.after(
            self.INTERVALO_VERIFICACAO_MS,
            self._verificar,
        )

    def _verificar(self) -> None:
        self._job_id = None
        if not janela_ui_ainda_ativa(self._janela):
            return
        try:
            opcoes = self._config.carregar_relatorio_automatico_carteira()
            if opcoes.habilitado and opcoes.horarios:
                agora = datetime.now()
                if self._data_executada != agora.date():
                    self._slots_executados_hoje.clear()
                    self._data_executada = agora.date()

                for horario in opcoes.horarios:
                    partes = horario.split(":")
                    if len(partes) != 2:
                        continue
                    hora = int(partes[0])
                    minuto = int(partes[1])
                    if agora.hour == hora and agora.minute == minuto:
                        chave = f"{agora.strftime('%d-%m-%Y')} {horario}"
                        if chave not in self._slots_executados_hoje:
                            self._slots_executados_hoje.add(chave)
                            self._ao_gerar()
                        break
        finally:
            self._agendar_verificacao()
