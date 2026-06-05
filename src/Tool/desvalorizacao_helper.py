"""Identifica quedas de preco (pico → fundo) em uma serie historica."""
from __future__ import annotations

from src.Model.cotacao import PontoHistorico
from src.Model.desvalorizacao import AnaliseDesvalorizacao, EventoDesvalorizacao


def listar_desvalorizacoes(pontos: list[PontoHistorico]) -> list[EventoDesvalorizacao]:
    """Lista cada queda entre um topo local e o fundo seguinte."""
    if len(pontos) < 2:
        return []

    eventos: list[EventoDesvalorizacao] = []
    indice_pico = 0
    preco_pico = float(pontos[0].preco_fechamento)
    indice_fundo = 0
    preco_fundo = preco_pico
    em_queda = False

    for indice in range(1, len(pontos)):
        preco = float(pontos[indice].preco_fechamento)

        if preco >= preco_pico:
            if em_queda and preco_pico > preco_fundo:
                eventos.append(
                    _montar_evento(pontos, indice_pico, indice_fundo, preco_pico, preco_fundo)
                )
            indice_pico = indice
            preco_pico = preco
            indice_fundo = indice
            preco_fundo = preco
            em_queda = False
            continue

        em_queda = True
        if preco < preco_fundo:
            preco_fundo = preco
            indice_fundo = indice

    if em_queda and preco_pico > preco_fundo:
        eventos.append(
            _montar_evento(pontos, indice_pico, indice_fundo, preco_pico, preco_fundo)
        )

    return eventos


def analisar_desvalorizacoes_periodo(
    pontos: list[PontoHistorico],
    simbolo: str,
    periodo_rotulo: str,
    moeda: str,
) -> AnaliseDesvalorizacao:
    """Monta a analise completa com todas as quedas e a ultima destacada."""
    codigo = simbolo.replace(".SA", "").replace("-USD", "")
    return AnaliseDesvalorizacao(
        simbolo=simbolo,
        codigo_exibicao=codigo,
        periodo_rotulo=periodo_rotulo,
        moeda=moeda,
        eventos=listar_desvalorizacoes(pontos),
    )


def _montar_evento(
    pontos: list[PontoHistorico],
    indice_pico: int,
    indice_fundo: int,
    preco_pico: float,
    preco_fundo: float,
) -> EventoDesvalorizacao:
    base = preco_pico if preco_pico else 1.0
    variacao_pct = ((preco_fundo - preco_pico) / base) * 100
    return EventoDesvalorizacao(
        data_pico=pontos[indice_pico].data_exibicao,
        data_fundo=pontos[indice_fundo].data_exibicao,
        preco_pico=round(preco_pico, 4),
        preco_fundo=round(preco_fundo, 4),
        variacao_percentual=round(variacao_pct, 2),
        variacao_valor=round(preco_fundo - preco_pico, 4),
        pregões=abs(indice_fundo - indice_pico) + 1,
    )
