"""Provedor de backup 1: Brapi (acoes da B3, sem token obrigatorio)."""
from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

from src.Model.cotacao import CotacaoResumo, PontoHistorico, SerieHistorica
from src.Service.mapeamento_periodo import MAPEAMENTO_PERIODO_BRAPI
from src.Service.provedores.util_provedor import (
    codigo_brapi,
    data_para_exibicao,
    eh_acao_b3,
    requisicao_json,
    timestamp_para_data,
)
from src.Tool.registrador_log import RegistradorLog

NOME_PROVEDOR = "Brapi"
URL_BASE = "https://brapi.dev/api"


class ProvedorBrapi:
    """Cotacoes e historico para tickers .SA via brapi.dev."""

    nome = NOME_PROVEDOR

    def __init__(self) -> None:
        self._log = RegistradorLog()

    def buscar_resumos(self, simbolos: list[str]) -> list[CotacaoResumo]:
        b3 = [s for s in simbolos if eh_acao_b3(s)]
        if not b3:
            return []

        codigos = ",".join(codigo_brapi(s) for s in b3)
        dados = requisicao_json(f"{URL_BASE}/quote/{quote(codigos)}", self._log)
        if not dados or not isinstance(dados, dict):
            return []

        mapa_simbolo = {codigo_brapi(s): s for s in b3}
        resultados: list[CotacaoResumo] = []

        for item in dados.get("results") or []:
            codigo = str(item.get("symbol", "")).upper()
            simbolo = mapa_simbolo.get(codigo)
            if not simbolo:
                continue
            resumo = self._item_para_resumo(simbolo, item)
            if resumo:
                resultados.append(resumo)
        return resultados

    def buscar_historico(
        self,
        simbolo: str,
        periodo_chave: str,
        data_inicio=None,
        data_fim=None,
    ) -> SerieHistorica | None:
        if not eh_acao_b3(simbolo):
            return None

        if periodo_chave == "personalizado":
            # Brapi nao expoe intervalo personalizado simples; usa 1y e filtra depois.
            cfg = {"range": "1y", "interval": "1d"}
            rotulo = "personalizado"
        else:
            cfg = MAPEAMENTO_PERIODO_BRAPI.get(periodo_chave, MAPEAMENTO_PERIODO_BRAPI["mes"])
            rotulo = periodo_chave

        codigo = codigo_brapi(simbolo)
        url = f"{URL_BASE}/quote/{quote(codigo)}?range={cfg['range']}&interval={cfg['interval']}"
        dados = requisicao_json(url, self._log)
        if not dados or not dados.get("results"):
            return None

        historico = dados["results"][0].get("historicalDataPrice") or []
        pontos: list[PontoHistorico] = []

        for barra in historico:
            try:
                data_obj = timestamp_para_data(barra["date"])
            except (KeyError, TypeError, ValueError):
                continue

            if periodo_chave == "personalizado" and data_inicio and data_fim:
                if data_obj.date() < data_inicio.date() or data_obj.date() > data_fim.date():
                    continue

            pontos.append(
                PontoHistorico(
                    data_iso=data_obj.isoformat(),
                    data_exibicao=data_para_exibicao(data_obj),
                    preco_fechamento=round(float(barra["close"]), 2),
                    preco_abertura=round(float(barra["open"]), 2),
                    volume=int(barra.get("volume") or 0) or None,
                )
            )

        if not pontos:
            return None
        return SerieHistorica(simbolo=simbolo, periodo=rotulo, pontos=pontos)

    def buscar_cotacao_detalhe(self, simbolo: str) -> dict | None:
        """Retorna JSON bruto da Brapi para montar tela Mais detalhes."""
        if not eh_acao_b3(simbolo):
            return None
        codigo = codigo_brapi(simbolo)
        return requisicao_json(f"{URL_BASE}/quote/{quote(codigo)}", self._log)

    @staticmethod
    def _item_para_resumo(simbolo: str, item: dict) -> CotacaoResumo | None:
        preco = item.get("regularMarketPrice")
        if preco is None:
            return None

        variacao_pct = float(item.get("regularMarketChangePercent") or 0)
        anterior = item.get("regularMarketPreviousClose")
        if anterior is not None:
            variacao_valor = float(preco) - float(anterior)
        else:
            variacao_valor = float(preco) * (variacao_pct / 100) if variacao_pct else 0.0

        volume = item.get("regularMarketVolume")
        return CotacaoResumo(
            simbolo=simbolo,
            nome=str(item.get("shortName") or item.get("longName") or simbolo.replace(".SA", "")),
            preco=round(float(preco), 2),
            variacao_percentual=round(variacao_pct, 2),
            variacao_valor=round(variacao_valor, 2),
            volume=int(volume) if volume is not None else None,
            moeda=str(item.get("currency") or "BRL"),
        )
