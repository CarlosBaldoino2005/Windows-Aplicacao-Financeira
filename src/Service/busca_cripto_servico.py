"""Busca de criptomoedas por nome ou codigo."""
import re

import yfinance as yf

from src.Model.cripto_universo import CRIPTOMOEDAS_MONITORADAS, NOMES_CRIPTO
from src.Model.resultado_busca import ResultadoBusca
from src.Tool.registrador_log import RegistradorLog
from src.Tool.texto_busca_helper import normalizar_texto_busca, texto_contem_busca
from src.Tool.validadores import normalizar_simbolo_cripto


class BuscaCriptoServico:
    """Localiza pares de cripto para pesquisa, favoritos e comparacao."""

    def __init__(self) -> None:
        self._log = RegistradorLog()

    def _buscar_lista_local(self, termo: str) -> list[ResultadoBusca]:
        encontrados: list[ResultadoBusca] = []
        vistos: set[str] = set()

        for simbolo in CRIPTOMOEDAS_MONITORADAS:
            codigo = simbolo.replace("-USD", "")
            nome = NOMES_CRIPTO.get(simbolo, codigo)
            if not texto_contem_busca(termo, simbolo, codigo, nome):
                continue
            ok, _ = normalizar_simbolo_cripto(simbolo)
            if not ok or ok in vistos:
                continue
            vistos.add(ok)
            encontrados.append(
                ResultadoBusca(simbolo=ok, nome=nome, bolsa="Cripto")
            )

        return encontrados

    def _buscar_yahoo(self, termo: str, limite: int) -> list[ResultadoBusca]:
        pesquisa = yf.Search(termo, max_results=limite * 3)
        pesquisa.search()
        resultados: list[ResultadoBusca] = []
        vistos: set[str] = set()

        for item in pesquisa.quotes or []:
            if item.get("quoteType") != "CRYPTOCURRENCY":
                continue
            simbolo_bruto = str(item.get("symbol", "")).strip().upper()
            if not simbolo_bruto:
                continue

            simbolo_ok, _ = normalizar_simbolo_cripto(simbolo_bruto)
            if not simbolo_ok or simbolo_ok in vistos:
                continue

            nome = str(item.get("longname") or item.get("shortname") or simbolo_ok)
            vistos.add(simbolo_ok)
            resultados.append(
                ResultadoBusca(simbolo=simbolo_ok, nome=nome, bolsa="Cripto")
            )
            if len(resultados) >= limite:
                break

        return resultados

    def buscar(self, termo: str, limite: int = 12) -> tuple[list[ResultadoBusca], str | None]:
        termo_limpo = termo.strip()
        termo_busca = normalizar_texto_busca(termo_limpo)
        if len(termo_busca) < 2:
            return [], "Digite ao menos 2 caracteres para pesquisar."

        agregado: dict[str, ResultadoBusca] = {}

        for item in self._buscar_lista_local(termo_limpo):
            agregado[item.simbolo] = item

        try:
            for item in self._buscar_yahoo(termo_busca, limite):
                agregado[item.simbolo] = item
        except Exception as exc:
            self._log.aviso(f"Busca Yahoo (cripto) indisponivel: {exc}")

        lista = list(agregado.values())[:limite]
        if not lista:
            return [], "Nenhuma cripto encontrada. Tente BTC, ETH ou SOL."
        return lista, None
