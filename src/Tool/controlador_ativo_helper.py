"""Resolve controlador de mercado conforme tipo do ativo monitorado."""
from __future__ import annotations

from typing import Any

from src.Model.monitoramento import TipoAtivoMonitoramento

_controladores: dict[TipoAtivoMonitoramento, Any] = {}


def inferir_tipo_ativo_monitoramento(simbolo: str, controlador: Any) -> TipoAtivoMonitoramento:
    """Deduz o tipo do ativo a partir do controlador e do simbolo Yahoo."""
    from src.Controller.controlador_cripto import ControladorCripto
    from src.Controller.controlador_dividendos import ControladorDividendos
    from src.Controller.controlador_etfs import ControladorEtfs
    from src.Controller.controlador_fiis import ControladorFiis
    from src.Tool.etfs_helper import eh_etf
    from src.Tool.fiis_helper import eh_fii

    if isinstance(controlador, ControladorCripto) or str(simbolo).endswith("-USD"):
        return "cripto"
    if isinstance(controlador, ControladorEtfs) or eh_etf(simbolo):
        return "etfs"
    if isinstance(controlador, ControladorFiis) or eh_fii(simbolo):
        return "fiis"
    if isinstance(controlador, ControladorDividendos):
        return "dividendos"
    return "acoes"


def obter_controlador_por_tipo(tipo_ativo: TipoAtivoMonitoramento) -> Any:
    """Retorna instancia unica do controlador adequado ao tipo."""
    if tipo_ativo in _controladores:
        return _controladores[tipo_ativo]

    if tipo_ativo == "cripto":
        from src.Controller.controlador_cripto import ControladorCripto

        controlador = ControladorCripto()
    elif tipo_ativo == "etfs":
        from src.Controller.controlador_etfs import ControladorEtfs

        controlador = ControladorEtfs()
    elif tipo_ativo == "fiis":
        from src.Controller.controlador_fiis import ControladorFiis

        controlador = ControladorFiis()
    elif tipo_ativo == "dividendos":
        from src.Controller.controlador_dividendos import ControladorDividendos

        controlador = ControladorDividendos()
    else:
        from src.Controller.controlador_mercado import ControladorMercado

        controlador = ControladorMercado()

    _controladores[tipo_ativo] = controlador
    return controlador
