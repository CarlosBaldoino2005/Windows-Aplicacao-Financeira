"""Converte modelos Python em JSON para o app mobile."""
from __future__ import annotations

from src.Model.cotacao import CotacaoResumo, PontoHistorico, SerieHistorica
from src.Model.resultado_busca import ResultadoBusca


def cotacao_para_dict(item: CotacaoResumo) -> dict:
    """Resumo de cotacao em formato JSON."""
    return {
        "simbolo": item.simbolo,
        "codigo": item.simbolo.replace(".SA", ""),
        "nome": item.nome,
        "preco": item.preco,
        "variacaoPercentual": item.variacao_percentual,
        "variacaoValor": item.variacao_valor,
        "volume": item.volume,
        "moeda": item.moeda,
    }


def lista_cotacoes_para_dict(itens: list[CotacaoResumo]) -> list[dict]:
    return [cotacao_para_dict(item) for item in itens]


def busca_para_dict(item: ResultadoBusca) -> dict:
    return {
        "simbolo": item.simbolo,
        "codigo": item.simbolo.replace(".SA", ""),
        "nome": item.nome,
        "bolsa": item.bolsa,
    }


def ponto_historico_para_dict(ponto: PontoHistorico) -> dict:
    return {
        "dataIso": ponto.data_iso,
        "data": ponto.data_exibicao,
        "precoFechamento": ponto.preco_fechamento,
        "precoAbertura": ponto.preco_abertura,
        "volume": ponto.volume,
    }


def serie_para_dict(serie: SerieHistorica) -> dict:
    return {
        "simbolo": serie.simbolo,
        "periodo": serie.periodo,
        "aviso": serie.aviso,
        "pontos": [ponto_historico_para_dict(p) for p in serie.pontos],
    }
