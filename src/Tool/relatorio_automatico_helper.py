"""Timer reutilizavel para relatorio PDF agendado (app aberta ou servico Windows)."""
from __future__ import annotations

import weakref

from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import executar_em_thread, janela_ui_ainda_ativa
from src.Tool.relatorio_agendado_executor import (
    INTERVALO_VERIFICACAO_SEGUNDOS,
    ResultadoRelatorioAgendado,
    executar_ciclo_relatorio_agendado,
    limpar_estado_agendamento_relatorio,
)

_registrados: list[weakref.ReferenceType["GerenciadorRelatorioAutomaticoCarteira"]] = []


def notificar_mudanca_configuracao_relatorio_automatico_carteira() -> None:
    """Reinicia agendadores apos salvar horarios na configuracao da carteira."""
    limpar_estado_agendamento_relatorio()
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

    def __init__(
        self,
        janela,
        ao_concluir=None,
        config: ConfigPainelIni | None = None,
        *,
        abrir_pdf: bool = True,
    ) -> None:
        self._janela = janela
        self._ao_concluir = ao_concluir
        self._config = config or ConfigPainelIni()
        self._abrir_pdf = abrir_pdf
        self._job_id: str | None = None
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
        """Mantido por compatibilidade ao salvar configuracao."""
        return

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
        atraso_ms = INTERVALO_VERIFICACAO_SEGUNDOS * 1000
        self._job_id = self._janela.after(atraso_ms, self._verificar)

    def _verificar(self) -> None:
        self._job_id = None
        if not janela_ui_ainda_ativa(self._janela):
            return

        def trabalho():
            return executar_ciclo_relatorio_agendado(abrir_pdf=self._abrir_pdf)

        def ao_fim(resultado: ResultadoRelatorioAgendado | None, erro_thread: str | None) -> None:
            if erro_thread:
                self._agendar_verificacao()
                return
            if (
                resultado is not None
                and resultado.executado
                and self._ao_concluir is not None
            ):
                self._ao_concluir(resultado)
            self._agendar_verificacao()

        executar_em_thread(self._janela, trabalho, ao_fim)
