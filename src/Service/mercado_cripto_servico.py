"""Busca cotacoes e historico de criptomoedas (Yahoo Finance)."""
from datetime import datetime

from src.Model.cotacao import CotacaoResumo, SerieHistorica
from src.Model.cripto_universo import (
    LIMITE_CRIPTO_PAINEL,
    montar_lista_cripto_monitoradas,
)
from src.Service.mercado_servico import _alinhar_series_comparacao
from src.Service.provedores.cadeia_mercado import CadeiaMercado
from src.Tool.registrador_log import RegistradorLog


class MercadoCriptoServico:
    """Regras de negocio para consulta de criptomoedas."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._cadeia = CadeiaMercado()

    def listar_monitoradas(self, quantidade: int = LIMITE_CRIPTO_PAINEL) -> list[str]:
        return montar_lista_cripto_monitoradas(quantidade)

    def buscar_resumos(self, simbolos: list[str]) -> list[CotacaoResumo]:
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

    def listar_em_alta(self, quantidade: int = LIMITE_CRIPTO_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_monitoradas(quantidade))
        em_alta = [r for r in resumos if r.variacao_percentual > 0]
        em_alta.sort(key=lambda item: item.variacao_percentual, reverse=True)
        return em_alta[:quantidade]

    def listar_em_queda(self, quantidade: int = LIMITE_CRIPTO_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_monitoradas(quantidade))
        em_queda = [r for r in resumos if r.variacao_percentual < 0]
        em_queda.sort(key=lambda item: item.variacao_percentual)
        return em_queda[:quantidade]

    def listar_todas_monitoradas(self, quantidade: int = LIMITE_CRIPTO_PAINEL) -> list[CotacaoResumo]:
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
        return self._cadeia.buscar_historico(simbolo, periodo_chave, data_inicio, data_fim)

    def comparar_criptos(
        self,
        simbolos: list[str],
        periodo_chave: str = "mes",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> dict:
        series_brutas: dict[str, list[dict]] = {}
        avisos: list[str] = []

        for simbolo in simbolos:
            serie = self.buscar_historico(simbolo, periodo_chave, data_inicio, data_fim)
            if not serie or not serie.pontos:
                codigo = simbolo.replace("-USD", "")
                avisos.append(f"Sem historico no periodo: {codigo}")
                continue

            series_brutas[simbolo] = [
                {
                    "data": p.data_exibicao,
                    "data_iso": p.data_iso,
                    "preco": p.preco_fechamento,
                }
                for p in serie.pontos
            ]

        alinhadas, avisos_alinhamento = _alinhar_series_comparacao(series_brutas, simbolos)
        avisos.extend(avisos_alinhamento)

        return {
            "simbolos": [s for s in simbolos if s in alinhadas],
            "series": alinhadas,
            "avisos": avisos,
        }
