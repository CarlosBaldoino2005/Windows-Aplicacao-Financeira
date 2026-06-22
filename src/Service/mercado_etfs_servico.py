"""Painel de ETFs (mesma logica do mercado, lista filtrada)."""
from datetime import datetime

from src.Model.cotacao import CotacaoResumo, SerieHistorica
from src.Model.etfs_universo import LIMITE_ETFS_PAINEL, montar_lista_etfs_monitorados
from src.Service.mercado_servico import MercadoServico
from src.Tool.etfs_helper import eh_etf


class MercadoEtfsServico:
    """Cotacoes e historico apenas para ETFs."""

    def __init__(self) -> None:
        self._mercado = MercadoServico()

    def listar_monitoradas(self, quantidade: int = LIMITE_ETFS_PAINEL) -> list[str]:
        return montar_lista_etfs_monitorados(quantidade)

    def buscar_resumos(self, simbolos: list[str]) -> list[CotacaoResumo]:
        if not simbolos:
            return []
        resumos = self._mercado.buscar_resumos(simbolos)
        return [r for r in resumos if eh_etf(r.simbolo)]

    def listar_em_alta(self, quantidade: int = LIMITE_ETFS_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_monitoradas(quantidade))
        em_alta = [r for r in resumos if r.variacao_percentual > 0]
        em_alta.sort(key=lambda item: item.variacao_percentual, reverse=True)
        return em_alta[:quantidade]

    def listar_em_queda(self, quantidade: int = LIMITE_ETFS_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_monitoradas(quantidade))
        em_queda = [r for r in resumos if r.variacao_percentual < 0]
        em_queda.sort(key=lambda item: item.variacao_percentual)
        return em_queda[:quantidade]

    def listar_todas_monitoradas(self, quantidade: int = LIMITE_ETFS_PAINEL) -> list[CotacaoResumo]:
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
        if not eh_etf(simbolo):
            return None
        return self._mercado.buscar_historico(simbolo, periodo_chave, data_inicio, data_fim)

    def comparar_acoes(
        self,
        simbolos: list[str],
        periodo_chave: str = "mes",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> dict:
        etfs = [s for s in simbolos if eh_etf(s)]
        return self._mercado.comparar_acoes(etfs, periodo_chave, data_inicio, data_fim)
