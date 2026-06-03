"""Orquestra Yahoo, Brapi e Yahoo Chart com fallback automatico."""
from __future__ import annotations

from src.Model.cotacao import CotacaoResumo, SerieHistorica
from src.Service.provedores.provedor_brapi import ProvedorBrapi
from src.Service.provedores.provedor_yahoo_chart import ProvedorYahooChart
from src.Service.provedores.provedor_yfinance import ProvedorYfinance
from src.Tool.registrador_log import RegistradorLog


class CadeiaMercado:
    """
    Tenta provedores em ordem:
    1) Yahoo Finance (yfinance)
    2) Brapi (B3)
    3) Yahoo Chart API (REST)
    """

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._cotacoes = [ProvedorYfinance(), ProvedorBrapi(), ProvedorYahooChart()]
        self._historico = [ProvedorYfinance(), ProvedorBrapi(), ProvedorYahooChart()]

    def buscar_resumos(self, simbolos: list[str]) -> list[CotacaoResumo]:
        if not simbolos:
            return []

        obtidos: dict[str, CotacaoResumo] = {}
        pendentes = list(simbolos)

        for provedor in self._cotacoes:
            if not pendentes:
                break
            try:
                lote = provedor.buscar_resumos(pendentes)
            except Exception as exc:
                self._log.aviso(f"Provedor {provedor.nome} falhou no lote: {exc}")
                continue

            for resumo in lote:
                if resumo.simbolo not in obtidos:
                    obtidos[resumo.simbolo] = resumo
                    self._log.info(f"Cotacao {resumo.simbolo} obtida via {provedor.nome}")

            pendentes = [s for s in pendentes if s not in obtidos]

        if pendentes:
            self._log.aviso(
                "Sem cotacao para: " + ", ".join(p.replace(".SA", "") for p in pendentes[:10])
                + ("..." if len(pendentes) > 10 else "")
            )

        return list(obtidos.values())

    def buscar_historico(
        self,
        simbolo: str,
        periodo_chave: str = "mes",
        data_inicio=None,
        data_fim=None,
    ) -> SerieHistorica | None:
        for provedor in self._historico:
            try:
                serie = provedor.buscar_historico(simbolo, periodo_chave, data_inicio, data_fim)
            except Exception as exc:
                self._log.aviso(f"Provedor {provedor.nome} falhou no historico de {simbolo}: {exc}")
                serie = None

            if serie and serie.pontos:
                self._log.info(f"Historico {simbolo} ({periodo_chave}) via {provedor.nome}")
                return serie

        self._log.erro(f"Historico indisponivel para {simbolo} em todos os provedores.")
        return None
