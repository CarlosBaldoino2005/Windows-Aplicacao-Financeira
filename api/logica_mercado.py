"""Logica compartilhada de painel, cotacao e historico por tipo de ativo."""
from __future__ import annotations

from datetime import datetime

from src.Model.cotacao import CotacaoResumo, SerieHistorica
from src.Model.cripto_universo import QUANTIDADE_MAXIMA_CRIPTO, QUANTIDADE_PADRAO_CRIPTO
from src.Model.fiis_universo import QUANTIDADE_MAXIMA_FIIS, QUANTIDADE_PADRAO_FIIS
from src.Model.acoes_universo import QUANTIDADE_MAXIMA_PAINEL, QUANTIDADE_PADRAO_PAINEL
from src.Model.indices_universo import (
    INDICES_MERCADO,
    QUANTIDADE_MAXIMA_INDICES,
    QUANTIDADE_PADRAO_INDICES,
    listar_simbolos_indices,
)
from src.Service.mercado_cripto_servico import MercadoCriptoServico
from src.Service.mercado_fiis_servico import MercadoFiisServico
from src.Service.mercado_servico import MercadoServico
from src.Tool.fiis_helper import eh_fii
from src.Tool.validadores import normalizar_simbolo, normalizar_simbolo_cripto

TIPOS_PAINEL = frozenset({"acoes", "cripto", "fiis", "indices"})


def normalizar_tipo_painel(tipo: str) -> str:
    """Valida tipo do painel; padrao acoes."""
    valor = (tipo or "acoes").strip().lower()
    if valor in TIPOS_PAINEL:
        return valor
    return "acoes"


def limites_quantidade(tipo: str) -> tuple[int, int]:
    """Retorna quantidade padrao e maxima por tipo."""
    if tipo == "cripto":
        return QUANTIDADE_PADRAO_CRIPTO, QUANTIDADE_MAXIMA_CRIPTO
    if tipo == "fiis":
        return QUANTIDADE_PADRAO_FIIS, QUANTIDADE_MAXIMA_FIIS
    if tipo == "indices":
        return QUANTIDADE_PADRAO_INDICES, QUANTIDADE_MAXIMA_INDICES
    return QUANTIDADE_PADRAO_PAINEL, QUANTIDADE_MAXIMA_PAINEL


def montar_painel(tipo: str, quantidade: int) -> dict[str, list[CotacaoResumo]]:
    """Painel Em alta / Em queda / Todas conforme o tipo."""
    if tipo == "cripto":
        servico = MercadoCriptoServico()
        return {
            "emAlta": servico.listar_em_alta(quantidade),
            "emQueda": servico.listar_em_queda(quantidade),
            "todas": servico.listar_todas_monitoradas(quantidade),
        }
    if tipo == "fiis":
        servico = MercadoFiisServico()
        return {
            "emAlta": servico.listar_em_alta(quantidade),
            "emQueda": servico.listar_em_queda(quantidade),
            "todas": servico.listar_todas_monitoradas(quantidade),
        }
    if tipo == "indices":
        return _montar_painel_indices(quantidade)

    servico = MercadoServico()
    return {
        "emAlta": servico.listar_em_alta(quantidade),
        "emQueda": servico.listar_em_queda(quantidade),
        "todas": servico.listar_todas_monitoradas(quantidade),
    }


def _montar_painel_indices(quantidade: int) -> dict[str, list[CotacaoResumo]]:
    servico = MercadoServico()
    simbolos = listar_simbolos_indices(quantidade)
    resumos = servico.buscar_resumos(simbolos)
    nomes = {item.simbolo: item.nome for item in INDICES_MERCADO}

    for resumo in resumos:
        if not resumo.nome or resumo.nome == resumo.simbolo:
            resumo.nome = nomes.get(resumo.simbolo, resumo.nome)

    em_alta = sorted(
        [r for r in resumos if r.variacao_percentual > 0],
        key=lambda item: item.variacao_percentual,
        reverse=True,
    )
    em_queda = sorted(
        [r for r in resumos if r.variacao_percentual < 0],
        key=lambda item: item.variacao_percentual,
    )
    todas = sorted(resumos, key=lambda item: nomes.get(item.simbolo, item.simbolo))
    return {"emAlta": em_alta, "emQueda": em_queda, "todas": todas}


def buscar_cotacao(tipo: str, simbolo: str) -> CotacaoResumo | None:
    """Busca cotacao atual conforme o tipo."""
    if tipo == "cripto":
        simbolo_ok, erro = normalizar_simbolo_cripto(simbolo)
        if erro:
            raise ValueError(erro)
        resumos = MercadoCriptoServico().buscar_resumos([simbolo_ok])
        return resumos[0] if resumos else None

    if tipo == "fiis":
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            raise ValueError(erro)
        if not eh_fii(simbolo_ok):
            raise ValueError("Codigo informado nao e um fundo imobiliario (FII).")
        resumos = MercadoFiisServico().buscar_resumos([simbolo_ok])
        return resumos[0] if resumos else None

    if tipo == "indices":
        simbolo_ok = _normalizar_simbolo_indice(simbolo)
        if not simbolo_ok:
            raise ValueError("Indice nao reconhecido.")
        resumos = MercadoServico().buscar_resumos([simbolo_ok])
        return resumos[0] if resumos else None

    simbolo_ok, erro = normalizar_simbolo(simbolo)
    if erro:
        raise ValueError(erro)
    resumos = MercadoServico().buscar_resumos([simbolo_ok])
    return resumos[0] if resumos else None


def buscar_historico(
    tipo: str,
    simbolo: str,
    periodo: str,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
) -> SerieHistorica | None:
    """Serie historica conforme o tipo."""
    if tipo == "cripto":
        simbolo_ok, erro = normalizar_simbolo_cripto(simbolo)
        if erro:
            raise ValueError(erro)
        return MercadoCriptoServico().buscar_historico(simbolo_ok, periodo, data_inicio, data_fim)

    if tipo == "fiis":
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            raise ValueError(erro)
        if not eh_fii(simbolo_ok):
            raise ValueError("Codigo informado nao e um fundo imobiliario (FII).")
        return MercadoFiisServico().buscar_historico(simbolo_ok, periodo, data_inicio, data_fim)

    if tipo == "indices":
        simbolo_ok = _normalizar_simbolo_indice(simbolo)
        if not simbolo_ok:
            raise ValueError("Indice nao reconhecido.")
        return MercadoServico().buscar_historico(simbolo_ok, periodo, data_inicio, data_fim)

    simbolo_ok, erro = normalizar_simbolo(simbolo)
    if erro:
        raise ValueError(erro)
    return MercadoServico().buscar_historico(simbolo_ok, periodo, data_inicio, data_fim)


def _normalizar_simbolo_indice(simbolo: str) -> str | None:
    simbolo_ok = simbolo.strip().upper()
    simbolos_validos = {item.simbolo for item in INDICES_MERCADO}
    if simbolo_ok in simbolos_validos:
        return simbolo_ok
    simbolo_b3, erro = normalizar_simbolo(simbolo)
    if erro or simbolo_b3 not in simbolos_validos:
        return None
    return simbolo_b3
