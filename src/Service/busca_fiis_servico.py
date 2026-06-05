"""Busca restrita a fundos imobiliarios (FIIs)."""
from __future__ import annotations

from src.Model.resultado_busca import ResultadoBusca
from src.Service.busca_acoes_servico import BuscaAcoesServico
from src.Tool.fiis_helper import eh_fii


class BuscaFiisServico:
    """Filtra resultados da busca geral mantendo apenas FIIs."""

    def __init__(self) -> None:
        self._busca = BuscaAcoesServico()

    def buscar(self, termo: str) -> tuple[list[ResultadoBusca], str | None]:
        itens, erro = self._busca.buscar(termo)
        if erro:
            return [], erro
        if not itens:
            return [], "Nenhum fundo imobiliario encontrado para este termo."

        filtrados: list[ResultadoBusca] = []
        for item in itens:
            if eh_fii(item.simbolo):
                filtrados.append(item)

        if not filtrados:
            return [], (
                "Nenhum FII encontrado. Tente outro codigo "
                "(ex.: HGLG11, MXRF11, KNRI11, XPLG11)."
            )
        return filtrados, None
