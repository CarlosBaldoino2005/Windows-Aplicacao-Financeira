"""Timer reutilizavel para atualizar cotacoes conforme dados/painel.ini."""
from __future__ import annotations

import weakref
from collections.abc import Callable

from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import janela_ui_ainda_ativa

_registrados: list[weakref.ReferenceType["GerenciadorAtualizacaoAutomatica"]] = []


def notificar_mudanca_configuracao_atualizacao_automatica() -> None:
    """Reagenda todos os paineis abertos apos salvar configuracoes."""
    vivos: list[weakref.ReferenceType[GerenciadorAtualizacaoAutomatica]] = []
    for referencia in _registrados:
        gerenciador = referencia()
        if gerenciador is None:
            continue
        vivos.append(referencia)
        gerenciador.reagendar()
    _registrados.clear()
    _registrados.extend(vivos)


class GerenciadorAtualizacaoAutomatica:
    """Dispara callback periodicamente enquanto a janela existir e a opcao estiver ativa."""

    def __init__(
        self,
        janela,
        config: ConfigPainelIni | None,
        ao_atualizar: Callable[[], None],
    ) -> None:
        self._janela = janela
        self._config = config or ConfigPainelIni()
        self._ao_atualizar = ao_atualizar
        self._job_id: str | None = None
        self._referencia = weakref.ref(self)
        _registrados.append(self._referencia)

    def iniciar(self) -> None:
        self.reagendar()

    def parar(self) -> None:
        self._cancelar_timer()
        try:
            _registrados.remove(self._referencia)
        except ValueError:
            pass

    def reagendar(self) -> None:
        self._cancelar_timer()
        if not janela_ui_ainda_ativa(self._janela):
            return
        opcoes = self._config.carregar_atualizacao_automatica()
        if not opcoes.habilitada:
            return
        atraso_ms = max(1, opcoes.intervalo_segundos) * 1000
        self._job_id = self._janela.after(atraso_ms, self._disparar)

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
