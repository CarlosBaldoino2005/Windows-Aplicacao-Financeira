"""Busca de acoes por nome ou codigo (Yahoo + lista local; busca online com fallback)."""
import re

import yfinance as yf

from src.Model.resultado_busca import ResultadoBusca
from src.Model.acoes_universo import ACOES_B3_MONITORADAS, ACOES_EUA_MONITORADAS, ACOES_PADRAO
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import normalizar_simbolo

# Mesmas listas do painel + extras para busca local.
ACOES_B3_BUSCA = list(ACOES_B3_MONITORADAS)

ACOES_INTERNACIONAIS_BUSCA = list(ACOES_EUA_MONITORADAS) + [
    "GOOG",
    "BABA",
    "KO",
    "PEP",
]


class BuscaAcoesServico:
    """Localiza tickers para o usuario adicionar na comparacao."""

    def __init__(self) -> None:
        self._log = RegistradorLog()

    def _buscar_lista_local(self, termo: str) -> list[ResultadoBusca]:
        termo_upper = termo.upper().strip()
        encontrados: list[ResultadoBusca] = []
        vistos: set[str] = set()

        candidatos = ACOES_B3_BUSCA + ACOES_INTERNACIONAIS_BUSCA
        for codigo in candidatos:
            if termo_upper not in codigo and termo_upper not in codigo.replace("3", "").replace("4", ""):
                continue
            simbolo, _ = normalizar_simbolo(codigo)
            if not simbolo or simbolo in vistos:
                continue
            vistos.add(simbolo)
            bolsa = "B3" if simbolo.endswith(".SA") else "EUA"
            encontrados.append(ResultadoBusca(simbolo=simbolo, nome=codigo, bolsa=bolsa))

        for simbolo in ACOES_PADRAO:
            codigo = simbolo.replace(".SA", "")
            if termo_upper in codigo or termo_upper in simbolo.upper():
                if simbolo not in vistos:
                    vistos.add(simbolo)
                    bolsa = "B3" if simbolo.endswith(".SA") else "EUA"
                    encontrados.append(
                        ResultadoBusca(simbolo=simbolo, nome=codigo, bolsa=bolsa)
                    )
        return encontrados

    def _priorizar_b3(self, resultados: list[ResultadoBusca]) -> list[ResultadoBusca]:
        return sorted(resultados, key=lambda r: (0 if r.bolsa == "B3" else 1, r.simbolo))

    def _buscar_yahoo(self, termo: str, limite: int) -> list[ResultadoBusca]:
        pesquisa = yf.Search(termo, max_results=limite * 2)
        pesquisa.search()
        resultados: list[ResultadoBusca] = []
        vistos: set[str] = set()

        for item in pesquisa.quotes or []:
            if item.get("quoteType") not in ("EQUITY", "ETF"):
                continue
            simbolo_bruto = str(item.get("symbol", "")).strip().upper()
            if not simbolo_bruto:
                continue

            # Prioriza B3 (.SA); ignora CEDEARs de outras bolsas se houver .SA.
            if simbolo_bruto.endswith(".BA") or simbolo_bruto.endswith(".MX"):
                continue

            nome = str(item.get("longname") or item.get("shortname") or simbolo_bruto)
            exchange = str(item.get("exchDisp") or item.get("exchange") or "")

            if simbolo_bruto.endswith(".SA"):
                if not re.match(r"^[A-Z]{3,5}\d{1,2}\.SA$", simbolo_bruto):
                    continue
                bolsa = "B3"
                simbolo_final = simbolo_bruto
            elif re.match(r"^[A-Z]{1,5}$", simbolo_bruto):
                bolsa = "EUA"
                simbolo_final = simbolo_bruto
            else:
                continue

            if simbolo_final in vistos:
                continue
            vistos.add(simbolo_final)
            resultados.append(
                ResultadoBusca(simbolo=simbolo_final, nome=nome, bolsa=bolsa)
            )
            if len(resultados) >= limite:
                break

        return resultados

    def buscar(self, termo: str, limite: int = 12) -> tuple[list[ResultadoBusca], str | None]:
        termo_limpo = termo.strip()
        if len(termo_limpo) < 2:
            return [], "Digite ao menos 2 caracteres para pesquisar."

        agregado: dict[str, ResultadoBusca] = {}

        for item in self._buscar_lista_local(termo_limpo):
            agregado[item.simbolo] = item

        try:
            for item in self._buscar_yahoo(termo_limpo, limite):
                agregado[item.simbolo] = item
        except Exception as exc:
            self._log.aviso(
                f"Busca Yahoo indisponivel ({exc}). Resultados locais e backups de cotacao continuam ativos."
            )

        lista = self._priorizar_b3(list(agregado.values()))[:limite]
        if not lista:
            return [], "Nenhuma acao encontrada. Tente PETR4, VALE3 ou AAPL."
        return lista, None
