"""Painel de fundos imobiliarios (mesma logica do mercado, lista filtrada)."""
from datetime import datetime

from src.Model.cotacao import CotacaoResumo, SerieHistorica
from src.Model.fiis_universo import LIMITE_FIIS_PAINEL, montar_lista_fiis_monitorados
from src.Service.mercado_servico import MercadoServico
from src.Tool.fiis_helper import eh_fii


class MercadoFiisServico:
    """Cotacoes e historico apenas para FIIs."""

    def __init__(self) -> None:
        self._mercado = MercadoServico()

    def listar_monitoradas(self, quantidade: int = LIMITE_FIIS_PAINEL) -> list[str]:
        return montar_lista_fiis_monitorados(quantidade)

    def buscar_resumos(self, simbolos: list[str]) -> list[CotacaoResumo]:
        if not simbolos:
            return []
        resumos = self._mercado.buscar_resumos(simbolos)
        return [r for r in resumos if eh_fii(r.simbolo)]

    def listar_em_alta(self, quantidade: int = LIMITE_FIIS_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_monitoradas(quantidade))
        em_alta = [r for r in resumos if r.variacao_percentual > 0]
        em_alta.sort(key=lambda item: item.variacao_percentual, reverse=True)
        return em_alta[:quantidade]

    def listar_em_queda(self, quantidade: int = LIMITE_FIIS_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_monitoradas(quantidade))
        em_queda = [r for r in resumos if r.variacao_percentual < 0]
        em_queda.sort(key=lambda item: item.variacao_percentual)
        return em_queda[:quantidade]

    def listar_todas_monitoradas(self, quantidade: int = LIMITE_FIIS_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_monitoradas(quantidade))
        resumos.sort(key=lambda item: item.simbolo)
        return resumos[:quantidade]

    def buscar_historico(
        self,
        simbolo: str,
        periodo_chave: str = "mes",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> SerieHistorica | None:
        if not eh_fii(simbolo):
            return None
        return self._mercado.buscar_historico(simbolo, periodo_chave, data_inicio, data_fim)

    def comparar_acoes(
        self,
        simbolos: list[str],
        periodo_chave: str = "mes",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> dict:
        fiis = [s for s in simbolos if eh_fii(s)]
        return self._mercado.comparar_acoes(fiis, periodo_chave, data_inicio, data_fim)
