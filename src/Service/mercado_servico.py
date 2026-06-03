"""Busca cotacoes e historico com fallback automatico entre provedores."""
from datetime import datetime

from src.Model.acoes_universo import ACOES_MONITORADAS, ACOES_PADRAO, LIMITE_ACOES_PAINEL
from src.Model.cotacao import CotacaoResumo, SerieHistorica
from src.Service.provedores.cadeia_mercado import CadeiaMercado
from src.Tool.registrador_log import RegistradorLog


class MercadoServico:
    """Regras de negocio para consulta ao mercado (Yahoo -> Brapi -> Yahoo Chart)."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._cadeia = CadeiaMercado()

    def listar_acoes_padrao(self) -> list[str]:
        return self.listar_acoes_monitoradas()

    def listar_acoes_monitoradas(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[str]:
        from src.Model.acoes_universo import montar_lista_monitoradas

        return montar_lista_monitoradas(quantidade)

    def buscar_resumos(self, simbolos: list[str]) -> list[CotacaoResumo]:
        """Obtem resumo de varias acoes (em lotes para listas grandes)."""
        if not simbolos:
            return []

        tamanho_lote = 25
        if len(simbolos) <= tamanho_lote:
            return self._cadeia.buscar_resumos(simbolos)

        agregado: list[CotacaoResumo] = []
        for inicio in range(0, len(simbolos), tamanho_lote):
            lote = simbolos[inicio : inicio + tamanho_lote]
            agregado.extend(self._cadeia.buscar_resumos(lote))
        return agregado

    def listar_em_alta(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_acoes_monitoradas(quantidade))
        em_alta = [r for r in resumos if r.variacao_percentual > 0]
        em_alta.sort(key=lambda item: item.variacao_percentual, reverse=True)
        return em_alta[:quantidade]

    def listar_em_queda(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_acoes_monitoradas(quantidade))
        em_queda = [r for r in resumos if r.variacao_percentual < 0]
        em_queda.sort(key=lambda item: item.variacao_percentual)
        return em_queda[:quantidade]

    def listar_todas_monitoradas(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_acoes_monitoradas(quantidade))
        resumos.sort(key=lambda item: item.simbolo)
        return resumos[:quantidade]

    def buscar_historico(
        self,
        simbolo: str,
        periodo_chave: str = "mes",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> SerieHistorica | None:
        return self._cadeia.buscar_historico(simbolo, periodo_chave, data_inicio, data_fim)

    def comparar_acoes(
        self,
        simbolos: list[str],
        periodo_chave: str = "mes",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> dict:
        series: dict[str, list[dict]] = {}
        for simbolo in simbolos:
            serie = self.buscar_historico(simbolo, periodo_chave, data_inicio, data_fim)
            if not serie or not serie.pontos:
                continue

            primeiro = serie.pontos[0].preco_fechamento or 1
            series[simbolo] = [
                {
                    "data": p.data_exibicao,
                    "data_iso": p.data_iso,
                    "preco": p.preco_fechamento,
                    "indice_relativo": round((p.preco_fechamento / primeiro) * 100, 2),
                }
                for p in serie.pontos
            ]

        return {"simbolos": list(series.keys()), "series": series}
