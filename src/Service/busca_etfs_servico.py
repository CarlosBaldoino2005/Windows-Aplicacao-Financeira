"""Busca restrita a ETFs."""
from __future__ import annotations

from src.Model.etfs_universo import ETFS_B3, ETFS_INTERNACIONAIS
from src.Model.resultado_busca import ResultadoBusca
from src.Service.busca_acoes_servico import BuscaAcoesServico
from src.Tool.etfs_helper import eh_etf
from src.Tool.texto_busca_helper import normalizar_texto_busca, texto_contem_busca
from src.Tool.validadores import normalizar_simbolo


class BuscaEtfsServico:
    """Filtra resultados da busca geral mantendo apenas ETFs."""

    def __init__(self) -> None:
        self._busca = BuscaAcoesServico()

    def _buscar_lista_local(self, termo: str) -> list[ResultadoBusca]:
        encontrados: list[ResultadoBusca] = []
        vistos: set[str] = set()

        for codigo in [*ETFS_B3, *ETFS_INTERNACIONAIS]:
            if not texto_contem_busca(termo, codigo):
                continue
            if codigo in ETFS_B3:
                simbolo, _ = normalizar_simbolo(codigo)
                bolsa = "B3"
            else:
                simbolo = codigo.upper()
                bolsa = "EUA"
            if not simbolo or simbolo in vistos:
                continue
            vistos.add(simbolo)
            encontrados.append(
                ResultadoBusca(simbolo=simbolo, nome=codigo, bolsa=bolsa)
            )

        return encontrados

    def buscar(self, termo: str) -> tuple[list[ResultadoBusca], str | None]:
        termo_busca = normalizar_texto_busca(termo.strip())
        if len(termo_busca) < 2:
            return [], "Digite ao menos 2 caracteres para pesquisar."

        agregado: dict[str, ResultadoBusca] = {}

        for item in self._buscar_lista_local(termo):
            agregado[item.simbolo] = item

        itens, erro = self._busca.buscar(termo)
        if erro and not agregado:
            return [], erro

        for item in itens:
            if eh_etf(item.simbolo):
                agregado[item.simbolo] = item

        filtrados = list(agregado.values())
        if not filtrados:
            return [], (
                "Nenhum ETF encontrado. Tente outro codigo "
                "(ex.: BOVA11, SMAL11, SPY, QQQ)."
            )
        return filtrados, None
