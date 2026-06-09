"""Calculos de dividendos para posicoes da carteira."""
from __future__ import annotations

from datetime import datetime

from src.Model.detalhes_acao import PagamentoDividendo
from src.Tool.validadores import validar_data_ptbr


def calcular_dividendos_recebidos(
    pagamentos: list[PagamentoDividendo],
    data_compra_texto: str,
    quantidade: float,
    *,
    referencia: datetime | None = None,
) -> float:
    """Soma dividendos pagos desde a data de compra ate hoje."""
    data_compra, _ = validar_data_ptbr(data_compra_texto)
    if data_compra is None or quantidade <= 0:
        return 0.0

    hoje = referencia or datetime.now()
    total = 0.0
    inicio = data_compra.replace(hour=0, minute=0, second=0, microsecond=0)

    for item in pagamentos:
        data_pag, _ = validar_data_ptbr(item.data_pagamento)
        if data_pag is None or item.valor_por_cota <= 0:
            continue
        if data_pag < inicio or data_pag > hoje:
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

    from datetime import timedelta

    proxima = ultimo[0] + timedelta(days=intervalo_dias)
    valor_cota = ultimo[1].valor_por_cota
    return (
        proxima.strftime("%d/%m/%Y"),
        valor_cota,
        round(valor_cota * quantidade, 4),
    )
