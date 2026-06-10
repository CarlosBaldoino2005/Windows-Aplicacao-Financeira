"""Painel de FIIs ordenado por Dividend Yield (DY) no periodo."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from src.Model.cotacao import CotacaoResumo
from src.Model.periodos_mercado import rotulo_periodo_por_chave
from src.Service.mercado_fiis_servico import MercadoFiisServico
from src.Service.painel_periodo_servico import _resolver_listar_simbolos
from src.Tool.fiis_dy_helper import calcular_dy_fii_no_periodo
from src.Tool.registrador_log import RegistradorLog

_MAX_WORKERS = 4


class PainelDyFiisServico:
    """Lista FIIs com maior, menor e todos os DY no periodo escolhido."""

    def __init__(self, mercado: MercadoFiisServico | None = None) -> None:
        self._mercado = mercado or MercadoFiisServico()
        self._listar_simbolos = _resolver_listar_simbolos(self._mercado)
        self._log = RegistradorLog()

    def obter_painel(
        self,
        quantidade: int,
        periodo_chave: str,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> dict:
        simbolos = self._listar_simbolos(quantidade)
        resumos = self._listar_resumos_dy(
            simbolos, periodo_chave, data_inicio, data_fim
        )

        com_dy = [r for r in resumos if r.variacao_percentual > 0]
        maior_dy = sorted(
            com_dy, key=lambda item: item.variacao_percentual, reverse=True
        )
        menor_dy = sorted(com_dy, key=lambda item: item.variacao_percentual)
        todas = sorted(
            resumos, key=lambda item: item.variacao_percentual, reverse=True
        )

        rotulo = rotulo_periodo_por_chave(periodo_chave)
        if periodo_chave == "personalizado" and data_inicio and data_fim:
            rotulo = (
                f"{data_inicio.strftime('%d/%m/%Y')} a "
                f"{data_fim.strftime('%d/%m/%Y')}"
            )

        return {
            "em_alta": maior_dy[:quantidade],
            "em_queda": menor_dy[:quantidade],
            "todas": todas[:quantidade],
            "quantidade": quantidade,
            "periodo_chave": periodo_chave,
            "periodo_rotulo": rotulo,
            "total_com_dados": len(resumos),
        }

    def _listar_resumos_dy(
        self,
        simbolos: list[str],
        periodo_chave: str,
        data_inicio: datetime | None,
        data_fim: datetime | None,
    ) -> list[CotacaoResumo]:
        if not simbolos:
            return []

        base_por_simbolo = {
            r.simbolo: r for r in self._mercado.buscar_resumos(simbolos)
        }

        resumos: list[CotacaoResumo] = []
        if len(simbolos) <= 8:
            for simbolo in simbolos:
                item = self._resumo_dy_de_simbolo(
                    simbolo,
                    periodo_chave,
                    data_inicio,
                    data_fim,
                    base_por_simbolo.get(simbolo),
                )
                if item:
                    resumos.append(item)
            return resumos

        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            futuros = {
                executor.submit(
                    self._resumo_dy_de_simbolo,
                    simbolo,
                    periodo_chave,
                    data_inicio,
                    data_fim,
                    base_por_simbolo.get(simbolo),
                ): simbolo
                for simbolo in simbolos
            }
            for futuro in as_completed(futuros):
                try:
                    item = futuro.result()
                    if item:
                        resumos.append(item)
                except Exception as exc:
                    simbolo = futuros[futuro]
                    self._log.aviso(f"DY no periodo indisponivel para {simbolo}: {exc}")
        return resumos

    def _resumo_dy_de_simbolo(
        self,
        simbolo: str,
        periodo_chave: str,
        data_inicio: datetime | None,
        data_fim: datetime | None,
        base: CotacaoResumo | None,
    ) -> CotacaoResumo | None:
        if base is None or base.preco <= 0:
            return None

        metricas = calcular_dy_fii_no_periodo(
            simbolo,
            base.preco,
            periodo_chave,
            data_inicio,
            data_fim,
            base.moeda,
        )
        if metricas is None:
            return None

        dy_pct, total_proventos = metricas
        return CotacaoResumo(
            simbolo=simbolo,
            nome=base.nome,
            preco=base.preco,
            variacao_percentual=dy_pct,
            variacao_valor=total_proventos,
            volume=base.volume,
            moeda=base.moeda,
        )
