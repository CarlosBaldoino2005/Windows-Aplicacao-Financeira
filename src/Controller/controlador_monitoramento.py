"""Coordena monitoramento de precos entre interface e servicos de mercado."""
from __future__ import annotations

from src.Model.cotacao import CotacaoResumo
from src.Model.monitoramento import (
    MonitoramentoItem,
    MonitoramentoLinha,
    TipoAtivoMonitoramento,
    calcular_status_monitoramento,
)
from src.Service.busca_acoes_servico import BuscaAcoesServico
from src.Service.busca_cripto_servico import BuscaCriptoServico
from src.Service.busca_dividendos_servico import BuscaDividendosServico
from src.Service.busca_etfs_servico import BuscaEtfsServico
from src.Service.busca_fiis_servico import BuscaFiisServico
from src.Service.mercado_cripto_servico import MercadoCriptoServico
from src.Service.mercado_dividendos_servico import MercadoDividendosServico
from src.Service.mercado_etfs_servico import MercadoEtfsServico
from src.Service.mercado_fiis_servico import MercadoFiisServico
from src.Service.mercado_servico import MercadoServico
from src.Service.monitoramento_servico import MonitoramentoServico


class ControladorMonitoramento:
    """API usada pelas telas de alertas e monitoramento."""

    def __init__(self) -> None:
        self._persistencia = MonitoramentoServico()
        self._mercado_acoes = MercadoServico()
        self._mercado_cripto = MercadoCriptoServico()
        self._mercado_fiis = MercadoFiisServico()
        self._mercado_etfs = MercadoEtfsServico()
        self._mercado_dividendos = MercadoDividendosServico()
        self._busca_acoes = BuscaAcoesServico()
        self._busca_cripto = BuscaCriptoServico()
        self._busca_fiis = BuscaFiisServico()
        self._busca_etfs = BuscaEtfsServico()
        self._busca_dividendos = BuscaDividendosServico()

    def listar_itens(self) -> list[MonitoramentoItem]:
        return self._persistencia.listar()

    def normalizar_simbolo(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoMonitoramento,
    ) -> tuple[str | None, str | None]:
        return self._persistencia.normalizar_simbolo(simbolo, tipo_ativo)

    def obter_cotacao_ativo(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoMonitoramento,
    ) -> tuple[CotacaoResumo | None, str | None]:
        simbolo_ok, erro = self.normalizar_simbolo(simbolo, tipo_ativo)
        if erro or not simbolo_ok:
            return None, erro or "Simbolo invalido."

        resumos = self._buscar_resumos_por_tipo(tipo_ativo, [simbolo_ok])
        if not resumos:
            return None, "Cotacao indisponivel para validar os limites."

        return resumos[0], None

    def adicionar_item(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoMonitoramento,
        valor_baixo: float | None,
        valor_alto: float | None,
        *,
        preco_atual: float | None = None,
        moeda: str | None = None,
    ) -> tuple[MonitoramentoItem | None, str | None]:
        from src.Tool.validadores import validar_limites_monitoramento

        cotacao = None
        if preco_atual is None or preco_atual <= 0:
            cotacao, erro_cotacao = self.obter_cotacao_ativo(simbolo, tipo_ativo)
            if erro_cotacao or cotacao is None or cotacao.preco <= 0:
                return None, erro_cotacao or "Cotacao indisponivel para validar os limites."
            preco_atual = cotacao.preco
            moeda = cotacao.moeda

        moeda_ref = moeda or (cotacao.moeda if cotacao is not None else "BRL")
        erro_limites = validar_limites_monitoramento(
            valor_baixo,
            valor_alto,
            preco_atual,
            moeda_ref,
        )
        if erro_limites:
            return None, erro_limites

        return self._persistencia.adicionar(simbolo, tipo_ativo, valor_baixo, valor_alto)

    def obter_item(self, item_id: str) -> MonitoramentoItem | None:
        return self._persistencia.obter(item_id)

    def atualizar_limites_item(
        self,
        item_id: str,
        valor_baixo: float | None,
        valor_alto: float | None,
    ) -> tuple[MonitoramentoItem | None, str | None]:
        item = self._persistencia.obter(item_id)
        if item is None:
            return None, "Item de monitoramento nao encontrado."

        cotacao, erro_cotacao = self.obter_cotacao_ativo(item.simbolo, item.tipo_ativo)
        if erro_cotacao or cotacao is None or cotacao.preco <= 0:
            return None, erro_cotacao or "Cotacao indisponivel para validar os limites."

        from src.Tool.validadores import validar_limites_monitoramento

        erro_limites = validar_limites_monitoramento(
            valor_baixo,
            valor_alto,
            cotacao.preco,
            cotacao.moeda,
        )
        if erro_limites:
            return None, erro_limites

        return self._persistencia.atualizar_limites(item_id, valor_baixo, valor_alto)

    def definir_pausa_itens(
        self,
        ids: list[str],
        pausado: bool,
    ) -> tuple[int, str | None]:
        return self._persistencia.definir_pausa_varios(ids, pausado)

    def _buscar_resumos_por_tipo(
        self,
        tipo_ativo: TipoAtivoMonitoramento,
        simbolos: list[str],
    ) -> list[CotacaoResumo]:
        if not simbolos:
            return []
        if tipo_ativo == "cripto":
            return self._mercado_cripto.buscar_resumos(simbolos)
        if tipo_ativo == "fiis":
            return self._mercado_fiis.buscar_resumos(simbolos)
        if tipo_ativo == "etfs":
            return self._mercado_etfs.buscar_resumos(simbolos)
        if tipo_ativo == "dividendos":
            return self._mercado_dividendos.buscar_resumos(simbolos)
        return self._mercado_acoes.buscar_resumos(simbolos)

    def remover_item(self, item_id: str) -> tuple[bool, str | None]:
        return self._persistencia.remover(item_id)

    def remover_itens(self, ids: list[str]) -> tuple[int, str | None]:
        return self._persistencia.remover_varios(ids)

    def pesquisar_ativos(
        self,
        tipo_ativo: TipoAtivoMonitoramento,
        termo: str,
    ) -> tuple[list, str | None]:
        if tipo_ativo == "cripto":
            return self._busca_cripto.buscar(termo)
        if tipo_ativo == "fiis":
            return self._busca_fiis.buscar(termo)
        if tipo_ativo == "etfs":
            return self._busca_etfs.buscar(termo)
        if tipo_ativo == "dividendos":
            return self._busca_dividendos.buscar(termo)
        return self._busca_acoes.buscar(termo)

    def obter_linhas_monitoramento(self) -> tuple[list[MonitoramentoLinha], str | None]:
        itens = self._persistencia.listar()
        if not itens:
            return [], None

        por_tipo: dict[TipoAtivoMonitoramento, list[str]] = {
            "acoes": [],
            "cripto": [],
            "etfs": [],
            "fiis": [],
            "dividendos": [],
        }
        for item in itens:
            por_tipo[item.tipo_ativo].append(item.simbolo)

        cotacoes: dict[tuple[TipoAtivoMonitoramento, str], CotacaoResumo] = {}
        if por_tipo["acoes"]:
            for resumo in self._mercado_acoes.buscar_resumos(por_tipo["acoes"]):
                cotacoes[("acoes", resumo.simbolo)] = resumo
        if por_tipo["cripto"]:
            for resumo in self._mercado_cripto.buscar_resumos(por_tipo["cripto"]):
                cotacoes[("cripto", resumo.simbolo)] = resumo
        if por_tipo["fiis"]:
            for resumo in self._mercado_fiis.buscar_resumos(por_tipo["fiis"]):
                cotacoes[("fiis", resumo.simbolo)] = resumo
        if por_tipo["etfs"]:
            for resumo in self._mercado_etfs.buscar_resumos(por_tipo["etfs"]):
                cotacoes[("etfs", resumo.simbolo)] = resumo
        if por_tipo["dividendos"]:
            for resumo in self._mercado_dividendos.buscar_resumos(por_tipo["dividendos"]):
                cotacoes[("dividendos", resumo.simbolo)] = resumo

        linhas: list[MonitoramentoLinha] = []
        for item in itens:
            cotacao = cotacoes.get((item.tipo_ativo, item.simbolo))
            preco = cotacao.preco if cotacao is not None else None
            status = calcular_status_monitoramento(
                preco,
                item.valor_baixo,
                item.valor_alto,
                pausado=item.pausado,
            )
            linhas.append(
                MonitoramentoLinha(item=item, cotacao=cotacao, status=status)
            )

        return linhas, None
