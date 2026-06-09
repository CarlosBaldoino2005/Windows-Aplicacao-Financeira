"""Coordena carteira de investimentos entre interface e servicos."""
from __future__ import annotations

from src.Controller.controlador_monitoramento import ControladorMonitoramento
from src.Model.carteira import LinhaCarteira, PosicaoCarteira, TipoAtivoCarteira, tipo_carteira_para_monitoramento
from src.Model.cotacao import CotacaoResumo
from src.Model.monitoramento import TipoAtivoMonitoramento
from src.Service.carteira_servico import CarteiraServico
from src.Service.detalhes_acao_servico import DetalhesAcaoServico
from src.Service.mercado_cripto_servico import MercadoCriptoServico
from src.Service.mercado_fiis_servico import MercadoFiisServico
from src.Service.mercado_servico import MercadoServico
from src.Tool.carteira_dividendos_helper import (
    calcular_dividendos_recebidos,
    estimar_proximo_dividendo,
)
from src.Tool.config_painel import ConfigPainelIni


class ControladorCarteira:
    """API usada pela tela de carteira."""

    def __init__(self) -> None:
        self._persistencia = CarteiraServico()
        self._config = ConfigPainelIni()
        self._mercado_acoes = MercadoServico()
        self._mercado_cripto = MercadoCriptoServico()
        self._mercado_fiis = MercadoFiisServico()
        self._detalhes = DetalhesAcaoServico()
        self._monitoramento = ControladorMonitoramento()

    def listar_posicoes(self) -> list[PosicaoCarteira]:
        return self._persistencia.listar()

    def obter_posicao(self, posicao_id: str) -> PosicaoCarteira | None:
        return self._persistencia.obter(posicao_id)

    def adicionar_posicao(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoCarteira,
        quantidade_texto: str,
        preco_texto: str,
        data_compra: str,
    ) -> tuple[PosicaoCarteira | None, str | None]:
        quantidade, erro_qtd = self._persistencia.parse_quantidade(quantidade_texto)
        if erro_qtd:
            return None, erro_qtd
        preco, erro_preco = self._persistencia.parse_preco(preco_texto)
        if erro_preco:
            return None, erro_preco
        return self._persistencia.adicionar(
            simbolo,
            tipo_ativo,
            quantidade or 0,
            preco or 0,
            data_compra,
        )

    def atualizar_posicao(
        self,
        posicao_id: str,
        simbolo: str,
        tipo_ativo: TipoAtivoCarteira,
        quantidade_texto: str,
        preco_texto: str,
        data_compra: str,
    ) -> tuple[PosicaoCarteira | None, str | None]:
        quantidade, erro_qtd = self._persistencia.parse_quantidade(quantidade_texto)
        if erro_qtd:
            return None, erro_qtd
        preco, erro_preco = self._persistencia.parse_preco(preco_texto)
        if erro_preco:
            return None, erro_preco
        return self._persistencia.atualizar(
            posicao_id,
            simbolo,
            tipo_ativo,
            quantidade or 0,
            preco or 0,
            data_compra,
        )

    def registrar_venda(
        self,
        posicao_id: str,
        quantidade_texto: str,
    ) -> tuple[bool, str | None]:
        quantidade, erro = self._persistencia.parse_quantidade(quantidade_texto)
        if erro:
            return False, erro
        return self._persistencia.registrar_venda(posicao_id, quantidade or 0)

    def remover_posicao(self, posicao_id: str) -> tuple[bool, str | None]:
        return self._persistencia.remover(posicao_id)

    def carregar_variacao_monitoramento_pct(self) -> float:
        return self._config.carregar_carteira_variacao_monitoramento_pct()

    def salvar_variacao_monitoramento_pct(self, valor: float) -> None:
        from src.Tool.validadores import validar_percentual_carteira

        pct, erro = validar_percentual_carteira(str(valor))
        if erro or pct is None:
            return
        self._config.salvar_carteira_variacao_monitoramento_pct(pct)
        self._persistencia.resincronizar_monitoramento_todas()

    def pesquisar_ativos(
        self,
        tipo_ativo: TipoAtivoCarteira,
        termo: str,
    ) -> tuple[list, str | None]:
        tipo_mon: TipoAtivoMonitoramento = tipo_carteira_para_monitoramento(tipo_ativo)  # type: ignore[assignment]
        return self._monitoramento.pesquisar_ativos(tipo_mon, termo)

    def obter_linhas_carteira(self) -> tuple[list[LinhaCarteira], str | None]:
        posicoes = self._persistencia.listar()
        if not posicoes:
            return [], None

        por_tipo: dict[TipoAtivoCarteira, list[str]] = {
            "acoes": [],
            "cripto": [],
            "fiis": [],
            "indices": [],
        }
        for posicao in posicoes:
            por_tipo[posicao.tipo_ativo].append(posicao.simbolo)

        cotacoes: dict[tuple[TipoAtivoCarteira, str], CotacaoResumo] = {}
        for resumo in self._mercado_acoes.buscar_resumos(
            por_tipo["acoes"] + por_tipo["indices"]
        ):
            chave_acoes = ("acoes", resumo.simbolo)
            chave_indices = ("indices", resumo.simbolo)
            cotacoes[chave_acoes] = resumo
            cotacoes[chave_indices] = resumo
        for resumo in self._mercado_cripto.buscar_resumos(por_tipo["cripto"]):
            cotacoes[("cripto", resumo.simbolo)] = resumo
        for resumo in self._mercado_fiis.buscar_resumos(por_tipo["fiis"]):
            cotacoes[("fiis", resumo.simbolo)] = resumo

        linhas: list[LinhaCarteira] = []
        for posicao in posicoes:
            cotacao = cotacoes.get((posicao.tipo_ativo, posicao.simbolo))
            dividendos = 0.0
            prox_data = ""
            prox_valor_cota = None
            prox_total = None

            if posicao.tipo_ativo != "indices":
                detalhes, _ = self._detalhes.obter_detalhes(posicao.simbolo)
                if detalhes is not None:
                    dividendos = calcular_dividendos_recebidos(
                        detalhes.pagamentos_dividendos,
                        posicao.data_compra,
                        posicao.quantidade,
                    )
                    prox_data, prox_valor_cota, prox_total = estimar_proximo_dividendo(
                        detalhes.pagamentos_dividendos,
                        posicao.quantidade,
                    )

            linhas.append(
                LinhaCarteira(
                    posicao=posicao,
                    cotacao=cotacao,
                    dividendos_recebidos=dividendos,
                    proximo_dividendo_data=prox_data,
                    proximo_dividendo_valor_por_cota=prox_valor_cota,
                    proximo_dividendo_previsto=prox_total,
                )
            )

        return linhas, None
