"""Noticias focadas em criptomoedas via Yahoo Finance."""
from __future__ import annotations

from src.Service.busca_cripto_servico import BuscaCriptoServico
from src.Service.noticias_mercado_servico import NoticiasMercadoServico
from src.Tool.validadores import normalizar_simbolo_cripto

_FONTES_CRIPTO: list[tuple[str, str]] = [
    ("BTC-USD", "Bitcoin"),
    ("ETH-USD", "Ethereum"),
    ("SOL-USD", "Solana"),
    ("BNB-USD", "BNB"),
    ("XRP-USD", "Ripple"),
    ("DOGE-USD", "Dogecoin"),
]


class NoticiasCriptoServico(NoticiasMercadoServico):
    """Agrega manchetes de referencias de criptomoedas."""

    def __init__(self) -> None:
        self._busca_cripto = BuscaCriptoServico()
        super().__init__(fontes=list(_FONTES_CRIPTO), busca=self._busca_cripto)

    def _resolver_fontes_pesquisa(self, termo: str) -> list[tuple[str, str, str]]:
        vistos: set[str] = set()
        fontes: list[tuple[str, str, str]] = []

        def incluir(simbolo: str, nome_exibicao: str) -> None:
            if not simbolo or simbolo in vistos:
                return
            vistos.add(simbolo)
            fontes.append((simbolo, "Cripto", nome_exibicao))

        simbolo_direto, erro = normalizar_simbolo_cripto(termo)
        if not erro:
            rotulo = simbolo_direto.replace("-USD", "")
            incluir(simbolo_direto, rotulo)

        try:
            resultados, _msg = self._busca_cripto.buscar(termo)
        except Exception as exc:
            self._log.aviso(f"Busca de cripto para noticias falhou: {exc}")
            resultados = []

        for item in resultados[: self._LIMITE_SIMBOLOS_PESQUISA]:
            codigo = item.simbolo.replace("-USD", "")
            rotulo = f"{codigo} — {item.nome}"
            incluir(item.simbolo, rotulo)

        return fontes[: self._LIMITE_SIMBOLOS_PESQUISA]
