"""Converte modelos Python em JSON para o app mobile."""
from __future__ import annotations

from src.Model.cotacao import CotacaoResumo, PontoHistorico, SerieHistorica
from src.Model.detalhes_acao import ConcorrenteResumo, DetalhesAcao, PagamentoDividendo
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


def _dividendo_para_dict(item: PagamentoDividendo) -> dict:
    return {
        "dataPagamento": item.data_pagamento,
        "valorPorCota": item.valor_por_cota,
        "dataIso": item.data_iso,
    }


def _concorrente_para_dict(item: ConcorrenteResumo) -> dict:
    return {
        "codigo": item.codigo,
        "nome": item.nome,
        "moeda": item.moeda,
        "lucroLiquido": item.lucro_liquido,
        "margemLucro": item.margem_lucro,
        "receita": item.receita,
        "capitalizacao": item.capitalizacao,
        "precoAtual": item.preco_atual,
        "variacaoDiaPct": item.variacao_dia_pct,
    }


def detalhes_para_dict(item: DetalhesAcao) -> dict:
    """Pacote de detalhes para o app mobile."""
    return {
        "simbolo": item.simbolo,
        "codigo": item.codigo,
        "moeda": item.moeda,
        "nomeEmpresa": item.nome_empresa,
        "setor": item.setor,
        "industria": item.industria,
        "pais": item.pais,
        "site": item.site,
        "siteRi": item.site_ri,
        "descricao": item.descricao,
        "cnpj": item.cnpj,
        "enderecoLinha1": item.endereco_linha1,
        "enderecoLinha2": item.endereco_linha2,
        "cidade": item.cidade,
        "estado": item.estado,
        "cep": item.cep,
        "telefone": item.telefone,
        "bolsa": item.bolsa,
        "dirigentes": [{"nome": n, "cargo": c} for n, c in item.dirigentes],
        "filiais": item.filiais,
        "funcionarios": item.funcionarios,
        "precoAtual": item.preco_atual,
        "variacaoDiaPct": item.variacao_dia_pct,
        "indicadores": [{"rotulo": r, "valor": v} for r, v in item.indicadores],
        "calculosIndicadores": item.calculos_indicadores,
        "trimestres": [
            {
                "periodo": t.periodo,
                "receita": t.receita,
                "lucroLiquido": t.lucro_liquido,
                "ebitda": t.ebitda,
                "lucroOperacional": t.lucro_operacional,
            }
            for t in item.trimestres
        ],
        "anuais": [
            {
                "periodo": a.periodo,
                "receita": a.receita,
                "lucroLiquido": a.lucro_liquido,
                "ebitda": a.ebitda,
                "lucroOperacional": a.lucro_operacional,
            }
            for a in item.anuais
        ],
        "pagamentosDividendos": [_dividendo_para_dict(d) for d in item.pagamentos_dividendos],
        "concorrentes": [_concorrente_para_dict(c) for c in item.concorrentes],
        "avisos": item.avisos,
        "ehCripto": item.eh_cripto,
        "opinioesAnalistas": _opinioes_analistas_para_dict(item),
    }


def _opinioes_analistas_para_dict(item: DetalhesAcao) -> dict | None:
    pacote = item.opinioes_analistas
    if not pacote:
        return None
    resumo = pacote.resumo
    return {
        "notaMedia": resumo.recomendacao_media,
        "notaMediaTexto": resumo.recomendacao_texto,
        "notaMediaDescricao": resumo.nota_media_descricao,
        "totalAnalistas": resumo.quantidade_analistas,
        "compraForte": resumo.compra_forte,
        "compra": resumo.comprar,
        "manter": resumo.manter,
        "vender": resumo.vender,
        "vendaForte": resumo.venda_forte,
        "precoAlvoMedio": resumo.preco_alvo_medio,
        "precoAlvoAlto": resumo.preco_alvo_max,
        "precoAlvoBaixo": resumo.preco_alvo_min,
    }
