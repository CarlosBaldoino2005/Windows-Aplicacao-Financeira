"""Busca de acoes restrita a empresas que pagam dividendos."""
from __future__ import annotations

from src.Model.resultado_busca import ResultadoBusca
from src.Service.busca_acoes_servico import BuscaAcoesServico
from src.Tool.dividendos_helper import eh_pagadora_dividendos


class BuscaDividendosServico:
    """Filtra resultados da busca geral mantendo apenas pagadoras de dividendos."""

    def __init__(self) -> None:
        self._busca = BuscaAcoesServico()

    def buscar(self, termo: str) -> tuple[list[ResultadoBusca], str | None]:
        itens, erro = self._busca.buscar(termo)
        if erro:
            return [], erro
        if not itens:
            return [], "Nenhuma empresa pagadora de dividendos encontrada para este termo."

        filtrados: list[ResultadoBusca] = []
        for item in itens:
            if eh_pagadora_dividendos(item.simbolo):
                filtrados.append(item)

        if not filtrados:
            return [], (
                "Nenhuma empresa com dividendos encontrada. "
                "Tente outro codigo (ex.: PETR4, VALE3, ITUB4, TAEE11)."
            )
        return filtrados, None
