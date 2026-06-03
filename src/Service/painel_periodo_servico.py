"""Painel em alta / queda / todas com variacao no periodo selecionado."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from src.Model.cotacao import CotacaoResumo, SerieHistorica
from src.Model.periodos_mercado import rotulo_periodo_por_chave
from src.Service.mercado_servico import MercadoServico
from src.Tool.registrador_log import RegistradorLog

_MAX_WORKERS = 4


class PainelPeriodoServico:
    """Calcula desempenho das acoes entre o inicio e o fim do periodo escolhido."""

    def __init__(self, mercado: MercadoServico | None = None) -> None:
        self._mercado = mercado or MercadoServico()
        self._log = RegistradorLog()

    def obter_painel(
        self,
        quantidade: int,
        periodo_chave: str,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> dict:
        simbolos = self._mercado.listar_acoes_monitoradas(quantidade)
        resumos = self._listar_resumos_periodo(
            simbolos, periodo_chave, data_inicio, data_fim
        )
        em_alta = [r for r in resumos if r.variacao_percentual > 0]
        em_alta.sort(key=lambda item: item.variacao_percentual, reverse=True)
        em_queda = [r for r in resumos if r.variacao_percentual < 0]
        em_queda.sort(key=lambda item: item.variacao_percentual)
        todas = sorted(resumos, key=lambda item: item.simbolo)

        rotulo = rotulo_periodo_por_chave(periodo_chave)
        if periodo_chave == "personalizado" and data_inicio and data_fim:
            rotulo = (
                f"{data_inicio.strftime('%d/%m/%Y')} a "
                f"{data_fim.strftime('%d/%m/%Y')}"
            )

        return {
            "em_alta": em_alta[:quantidade],
            "em_queda": em_queda[:quantidade],
            "todas": todas[:quantidade],
            "quantidade": quantidade,
            "periodo_chave": periodo_chave,
            "periodo_rotulo": rotulo,
            "total_com_dados": len(resumos),
        }

    def _listar_resumos_periodo(
        self,
        simbolos: list[str],
        periodo_chave: str,
        data_inicio: datetime | None,
        data_fim: datetime | None,
    ) -> list[CotacaoResumo]:
        if not simbolos:
            return []

        base_por_simbolo = {
            r.simbolo: r
            for r in self._mercado.buscar_resumos(simbolos)
        }

        resumos: list[CotacaoResumo] = []
        if len(simbolos) <= 8:
            for simbolo in simbolos:
                item = self._resumo_de_simbolo_no_periodo(
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
                    self._resumo_de_simbolo_no_periodo,
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
                    self._log.aviso(
                        f"Variacao no periodo indisponivel para {simbolo}: {exc}"
                    )
        return resumos

    def _resumo_de_simbolo_no_periodo(
        self,
        simbolo: str,
        periodo_chave: str,
        data_inicio: datetime | None,
        data_fim: datetime | None,
        base: CotacaoResumo | None,
    ) -> CotacaoResumo | None:
        serie = self._mercado.buscar_historico(
            simbolo, periodo_chave, data_inicio, data_fim
        )
        metricas = self._metricas_do_periodo(serie)
        if metricas is None:
            return None

        preco_fim, var_valor, var_pct = metricas
        nome = base.nome if base else simbolo.replace(".SA", "")
        moeda = base.moeda if base else ("BRL" if simbolo.endswith(".SA") else "USD")
        volume = base.volume if base else None

        return CotacaoResumo(
            simbolo=simbolo,
            nome=nome,
            preco=round(preco_fim, 2),
            variacao_percentual=round(var_pct, 2),
            variacao_valor=round(var_valor, 2),
            volume=volume,
            moeda=moeda,
        )

    @staticmethod
    def _metricas_do_periodo(serie: SerieHistorica | None) -> tuple[float, float, float] | None:
        if serie is None or not serie.pontos or len(serie.pontos) < 2:
            return None
        preco_inicio = float(serie.pontos[0].preco_fechamento)
        preco_fim = float(serie.pontos[-1].preco_fechamento)
        if preco_inicio <= 0:
            return None
        var_valor = preco_fim - preco_inicio
        var_pct = (var_valor / preco_inicio) * 100
        return preco_fim, var_valor, var_pct
