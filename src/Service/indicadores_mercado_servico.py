"""Indicadores publicos do Banco Central (CDI, Selic) para renda fixa bancaria."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.Service.cdi_servico import CdiServico
from src.Service.provedores.util_provedor import requisicao_json
from src.Tool.registrador_log import RegistradorLog

CODIGO_SERIE_SELIC_DIARIA = 432
URL_SERIE_BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"


@dataclass
class IndicadoresMercado:
    cdi_aa_estimada: float | None
    selic_aa: float | None
    data_referencia_texto: str
    observacao: str = ""


class IndicadoresMercadoServico:
    """Consulta taxas de referencia no BCB para exibir no hub de renda fixa."""

    def __init__(self) -> None:
        self._cdi = CdiServico()
        self._log = RegistradorLog()
        self._cache: IndicadoresMercado | None = None

    def obter_indicadores(self, usar_cache: bool = True) -> IndicadoresMercado:
        if usar_cache and self._cache is not None:
            return self._cache

        hoje = date.today()
        cdi_aa = self._cdi.obter_cdi_anualizado_estimado()

        selic_aa = self._obter_ultima_selic_aa(hoje)

        obs = "Fonte: Banco Central do Brasil (series CDI diaria e Selic)."
        if cdi_aa is None and selic_aa is None:
            obs = "Nao foi possivel carregar indicadores do BCB no momento."

        self._cache = IndicadoresMercado(
            cdi_aa_estimada=cdi_aa,
            selic_aa=selic_aa,
            data_referencia_texto=hoje.strftime("%d/%m/%Y"),
            observacao=obs,
        )
        return self._cache

    def _obter_ultima_selic_aa(self, hoje: date) -> float | None:
        inicio = date(hoje.year, 1, 1)
        url = (
            URL_SERIE_BCB.format(codigo=CODIGO_SERIE_SELIC_DIARIA)
            + f"?formato=json&dataInicial={inicio.strftime('%d/%m/%Y')}"
            + f"&dataFinal={hoje.strftime('%d/%m/%Y')}"
        )
        dados = requisicao_json(url, log=self._log)
        if not isinstance(dados, list) or not dados:
            return None
        ultimo = dados[-1]
        if not isinstance(ultimo, dict):
            return None
        try:
            return round(float(str(ultimo.get("valor", "")).replace(",", ".")), 2)
        except (TypeError, ValueError):
            return None
