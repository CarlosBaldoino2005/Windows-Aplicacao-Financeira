"""Busca restrita a fundos imobiliarios (FIIs)."""
from __future__ import annotations

from src.Model.fiis_universo import FIIS_B3
from src.Model.resultado_busca import ResultadoBusca
from src.Service.busca_acoes_servico import BuscaAcoesServico
from src.Tool.fiis_helper import eh_fii
from src.Tool.texto_busca_helper import normalizar_texto_busca, texto_contem_busca
from src.Tool.validadores import normalizar_simbolo


class BuscaFiisServico:
    """Filtra resultados da busca geral mantendo apenas FIIs."""

    def __init__(self) -> None:
        self._busca = BuscaAcoesServico()

    def _buscar_lista_local(self, termo: str) -> list[ResultadoBusca]:
        encontrados: list[ResultadoBusca] = []
        vistos: set[str] = set()

        for codigo in FIIS_B3:
            if not texto_contem_busca(termo, codigo):
                continue
            simbolo, _ = normalizar_simbolo(codigo)
            if not simbolo or simbolo in vistos:
                continue
            vistos.add(simbolo)
            encontrados.append(
                ResultadoBusca(simbolo=simbolo, nome=codigo, bolsa="B3")
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
            if eh_fii(item.simbolo):
                agregado[item.simbolo] = item

        filtrados = list(agregado.values())
        if not filtrados:
            return [], (
                "Nenhum FII encontrado. Tente outro codigo "
                "(ex.: HGLG11, MXRF11, KNRI11, XPLG11)."
            )
        return filtrados, None
