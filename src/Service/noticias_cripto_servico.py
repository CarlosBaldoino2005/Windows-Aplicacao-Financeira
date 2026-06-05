"""Noticias focadas em criptomoedas via Yahoo Finance."""
from __future__ import annotations

from src.Model.provedores_noticias import CATEGORIA_CRIPTO, simbolo_permitido_no_provedor
from src.Service.busca_cripto_servico import BuscaCriptoServico
from src.Service.noticias_mercado_servico import NoticiasMercadoServico
from src.Tool.validadores import normalizar_simbolo_cripto

_LIMITE_SIMBOLOS_PESQUISA = 5


class NoticiasCriptoServico(NoticiasMercadoServico):
    """Agrega manchetes conforme o provedor de cripto escolhido no INI."""

    def __init__(self) -> None:
        self._busca_cripto = BuscaCriptoServico()
        super().__init__(busca=self._busca_cripto, categoria=CATEGORIA_CRIPTO)

    def _resolver_fontes_pesquisa(self, termo: str, provedor) -> list[tuple[str, str, str]]:
        vistos: set[str] = set()
        fontes: list[tuple[str, str, str]] = []

        def incluir(simbolo: str, nome_exibicao: str) -> None:
            if not simbolo or simbolo in vistos:
                return
            if not simbolo_permitido_no_provedor(simbolo, provedor):
                return
            vistos.add(simbolo)
            fontes.append((simbolo, "Cripto", nome_exibicao))

        simbolo_direto, erro = normalizar_simbolo_cripto(termo)
        if not erro:
            rotulo = simbolo_direto.replace("-USD", "")
            incluir(simbolo_direto, rotulo)

        try:
            resultados, _msg = self._busca_cripto.buscar(termo)
        except Exception:
            resultados = []

        for item in resultados[:_LIMITE_SIMBOLOS_PESQUISA]:
            if not simbolo_permitido_no_provedor(item.simbolo, provedor):
                continue
            codigo = item.simbolo.replace("-USD", "")
            rotulo = f"{codigo} — {item.nome}"
            incluir(item.simbolo, rotulo)

        return fontes[:_LIMITE_SIMBOLOS_PESQUISA]
