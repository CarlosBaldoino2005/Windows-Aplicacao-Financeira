"""Busca restrita a BDRs (acoes globais na B3)."""
from __future__ import annotations

import re

import yfinance as yf

from src.Model.acoes_bdr_universo import BDRS_B3
from src.Model.resultado_busca import ResultadoBusca
from src.Tool.bdrs_helper import eh_bdr_b3
from src.Tool.registrador_log import RegistradorLog
from src.Tool.texto_busca_helper import normalizar_texto_busca, texto_contem_busca
from src.Tool.validadores import normalizar_simbolo

_PADRAO_BDR_YAHOO = re.compile(r"^[A-Z]{4}3[245]\.SA$")


class BuscaAcoesGlobaisServico:
    """Filtra resultados mantendo apenas BDRs negociados na B3."""

    def __init__(self) -> None:
        self._log = RegistradorLog()

    def _buscar_lista_local(self, termo: str) -> list[ResultadoBusca]:
        encontrados: list[ResultadoBusca] = []
        vistos: set[str] = set()

        for codigo in BDRS_B3:
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

    def _buscar_yahoo(self, termo: str, limite: int) -> list[ResultadoBusca]:
        pesquisa = yf.Search(termo, max_results=limite * 3)
        pesquisa.search()
        resultados: list[ResultadoBusca] = []
        vistos: set[str] = set()

        for item in pesquisa.quotes or []:
            if item.get("quoteType") != "EQUITY":
                continue
            simbolo_bruto = str(item.get("symbol", "")).strip().upper()
            if not simbolo_bruto.endswith(".SA"):
                continue
            if not _PADRAO_BDR_YAHOO.match(simbolo_bruto) and not eh_bdr_b3(simbolo_bruto):
                continue

            nome = str(item.get("longname") or item.get("shortname") or simbolo_bruto)
            if simbolo_bruto in vistos:
                continue
            vistos.add(simbolo_bruto)
            resultados.append(
                ResultadoBusca(simbolo=simbolo_bruto, nome=nome, bolsa="B3")
            )
            if len(resultados) >= limite:
                break

        return resultados

    def buscar(self, termo: str, limite: int = 12) -> tuple[list[ResultadoBusca], str | None]:
        termo_busca = normalizar_texto_busca(termo.strip())
        if len(termo_busca) < 2:
            return [], "Digite ao menos 2 caracteres para pesquisar."

        agregado: dict[str, ResultadoBusca] = {}

        for item in self._buscar_lista_local(termo):
            agregado[item.simbolo] = item

        try:
            for item in self._buscar_yahoo(termo_busca, limite):
                agregado[item.simbolo] = item
        except Exception as exc:
            self._log.aviso(
                f"Busca Yahoo indisponivel ({exc}). Resultados locais continuam ativos."
            )

        filtrados = list(agregado.values())
        if not filtrados:
            return [], (
                "Nenhum BDR encontrado. Tente AAPL34, MSFT34, GOGL34 ou o nome da empresa."
            )
        return filtrados[:limite], None
