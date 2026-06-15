"""
Servico Windows: relatorio automatico da carteira com app fechada.

Instalar (como administrador):
  scripts\\instalar_servico_relatorio.bat

Desinstalar:
  scripts\\desinstalar_servico_relatorio.bat
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import win32event
import win32service
import win32serviceutil
import servicemanager

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
NOME_SERVICO = "FinanceiroRelatorioCarteira"
NOME_EXIBICAO = "Financeiro - Relatorio automatico da carteira"
DESCRICAO = (
    "Gera o PDF da carteira e envia por e-mail nos horarios definidos em dados/painel.ini."
)


def _preparar_ambiente() -> None:
    os.chdir(RAIZ_PROJETO)
    raiz = str(RAIZ_PROJETO)
    if raiz not in sys.path:
        sys.path.insert(0, raiz)
    os.environ.setdefault("PYTHONPATH", raiz)


class ServicoRelatorioCarteiraWindows(win32serviceutil.ServiceFramework):
    _svc_name_ = NOME_SERVICO
    _svc_display_name_ = NOME_EXIBICAO
    _svc_description_ = DESCRICAO

    def __init__(self, args) -> None:
        win32serviceutil.ServiceFramework.__init__(self, args)
        self._parar_evento = win32event.CreateEvent(None, 0, 0, None)
        self._ativo = True

    def SvcStop(self) -> None:
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self._ativo = False
        win32event.SetEvent(self._parar_evento)

    def SvcDoRun(self) -> None:
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        self._executar_loop()

    def _executar_loop(self) -> None:
        from src.Tool.registrador_log import RegistradorLog
        from src.Tool.relatorio_agendado_executor import (
            INTERVALO_VERIFICACAO_SEGUNDOS,
            executar_ciclo_relatorio_agendado,
        )

        _preparar_ambiente()
        log = RegistradorLog(RAIZ_PROJETO)
        log.info("Servico Windows de relatorio da carteira iniciado.")

        while self._ativo:
            try:
                executar_ciclo_relatorio_agendado(pasta_base=RAIZ_PROJETO)
            except Exception as exc:
                log.erro(f"Servico relatorio carteira: {exc}")

            intervalo_ms = INTERVALO_VERIFICACAO_SEGUNDOS * 1000
            resultado = win32event.WaitForSingleObject(self._parar_evento, intervalo_ms)
            if resultado == win32event.WAIT_OBJECT_0:
                break

        log.info("Servico Windows de relatorio da carteira encerrado.")


def main() -> None:
    _preparar_ambiente()
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ServicoRelatorioCarteiraWindows)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ServicoRelatorioCarteiraWindows)


if __name__ == "__main__":
    main()
