"""Calculos de dividendos para posicoes da carteira."""
from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timedelta

from src.Model.detalhes_acao import PagamentoDividendo
from src.Tool.validadores import validar_data_ptbr


def calcular_dividendos_recebidos(
    pagamentos: list[PagamentoDividendo],
    data_compra_texto: str,
    quantidade: float,
    *,
    referencia: datetime | None = None,
    data_fim_texto: str | None = None,
) -> float:
    """Soma dividendos pagos desde a data de compra ate hoje."""
    data_compra, _ = validar_data_ptbr(data_compra_texto)
    if data_compra is None or quantidade <= 0:
        return 0.0

    hoje = referencia or datetime.now()
    fim = hoje
    if data_fim_texto:
        data_fim, _ = validar_data_ptbr(data_fim_texto)
        if data_fim is not None:
            fim = data_fim.replace(hour=23, minute=59, second=59, microsecond=999999)

    total = 0.0
    inicio = data_compra.replace(hour=0, minute=0, second=0, microsecond=0)

    for item in pagamentos:
        data_pag, _ = validar_data_ptbr(item.data_pagamento)
        if data_pag is None or item.valor_por_cota <= 0:
            continue
        if data_pag < inicio or data_pag > fim:
            continue
        total += item.valor_por_cota * quantidade

    return round(total, 4)


def estimar_proximo_dividendo(
    pagamentos: list[PagamentoDividendo],
    quantidade: float,
    *,
    referencia: datetime | None = None,
) -> tuple[str, float | None, float | None]:
    """
    Estima proxima data e valor com base no historico.
    Retorna (data_texto, valor_por_cota, valor_total_previsto).
    """
    if not pagamentos or quantidade <= 0:
        return "", None, None

    hoje = referencia or datetime.now()
    ordenados: list[tuple[datetime, PagamentoDividendo]] = []

    for item in pagamentos:
        data_pag, _ = validar_data_ptbr(item.data_pagamento)
        if data_pag is None or item.valor_por_cota <= 0:
            continue
        ordenados.append((data_pag, item))

    if not ordenados:
        return "", None, None

    ordenados.sort(key=lambda par: par[0], reverse=True)

    for data_pag, item in ordenados:
        if data_pag > hoje:
            return (
                item.data_pagamento,
                item.valor_por_cota,
                round(item.valor_por_cota * quantidade, 4),
            )

    ultimo = ordenados[0]
    intervalo_dias = 90
    if len(ordenados) >= 2:
        difs: list[int] = []
        for indice in range(min(4, len(ordenados) - 1)):
            difs.append(abs((ordenados[indice][0] - ordenados[indice + 1][0]).days))
        if difs:
            intervalo_dias = max(30, int(sum(difs) / len(difs)))

    proxima = ultimo[0] + timedelta(days=intervalo_dias)
    valor_cota = ultimo[1].valor_por_cota
    return (
        proxima.strftime("%d/%m/%Y"),
        valor_cota,
        round(valor_cota * quantidade, 4),
    )


def _limites_proximo_mes_calendario(referencia: datetime) -> tuple[datetime, datetime]:
    """Primeiro e ultimo instante do mes calendario seguinte a referencia."""
    if referencia.month == 12:
        ano, mes = referencia.year + 1, 1
    else:
        ano, mes = referencia.year, referencia.month + 1
    inicio = datetime(ano, mes, 1)
    ultimo_dia = monthrange(ano, mes)[1]
    fim = datetime(ano, mes, ultimo_dia, 23, 59, 59)
    return inicio, fim


def _intervalo_medio_pagamentos(
    ordenados: list[tuple[datetime, PagamentoDividendo]],
) -> int:
    """Intervalo medio em dias entre pagamentos recentes (minimo 30)."""
    if len(ordenados) < 2:
        return 90
    difs: list[int] = []
    for indice in range(min(4, len(ordenados) - 1)):
        difs.append(abs((ordenados[indice][0] - ordenados[indice + 1][0]).days))
    if not difs:
        return 90
    return max(30, int(sum(difs) / len(difs)))


def _pagamentos_ordenados(
    pagamentos: list[PagamentoDividendo],
) -> list[tuple[datetime, PagamentoDividendo]]:
    ordenados: list[tuple[datetime, PagamentoDividendo]] = []
    for item in pagamentos:
        data_pag, _ = validar_data_ptbr(item.data_pagamento)
        if data_pag is None or item.valor_por_cota <= 0:
            continue
        ordenados.append((data_pag, item))
    ordenados.sort(key=lambda par: par[0], reverse=True)
    return ordenados


def estimar_dividendo_proximo_mes(
    pagamentos: list[PagamentoDividendo],
    quantidade: float,
    *,
    referencia: datetime | None = None,
) -> float | None:
    """
    Valor total previsto de dividendos no proximo mes calendario.
    Usa pagamentos ja anunciados, a proxima data estimada ou projecao pelo intervalo medio.
    """
    if not pagamentos or quantidade <= 0:
        return None

    hoje = referencia or datetime.now()
    inicio_mes, fim_mes = _limites_proximo_mes_calendario(hoje)

    total_anunciado = 0.0
    tem_anunciado = False
    for item in pagamentos:
        data_pag, _ = validar_data_ptbr(item.data_pagamento)
        if data_pag is None or item.valor_por_cota <= 0:
            continue
        if data_pag > hoje and inicio_mes <= data_pag <= fim_mes:
            total_anunciado += item.valor_por_cota * quantidade
            tem_anunciado = True
    if tem_anunciado:
        return round(total_anunciado, 4)

    prox_data, _, prox_total = estimar_proximo_dividendo(
        pagamentos, quantidade, referencia=hoje
    )
    if prox_data and prox_total is not None:
        data_prox, _ = validar_data_ptbr(prox_data)
        if data_prox and inicio_mes <= data_prox <= fim_mes:
            return prox_total

    ordenados = _pagamentos_ordenados(pagamentos)
    if not ordenados:
        return None

    ultimo_data, ultimo_item = ordenados[0]
    intervalo_dias = _intervalo_medio_pagamentos(ordenados)
    candidata = ultimo_data
    while candidata <= fim_mes:
        candidata = candidata + timedelta(days=intervalo_dias)
        if inicio_mes <= candidata <= fim_mes:
            return round(ultimo_item.valor_por_cota * quantidade, 4)
        if candidata > fim_mes:
            break

    return None
