"""Busca composicao da carteira de ETFs via Yahoo Finance."""
from __future__ import annotations

import yfinance as yf

from src.Model.composicao_etf import AtivoComposicaoEtf, ComposicaoEtf
from src.Model.etf_proxies_composicao import obter_proxy_composicao
from src.Tool.etfs_helper import eh_etf
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import normalizar_simbolo


class ComposicaoEtfServico:
    """Obtem principais posicoes (top holdings) reportadas no Yahoo."""

    def __init__(self) -> None:
        self._log = RegistradorLog()

    def obter_composicao(self, simbolo: str) -> tuple[ComposicaoEtf | None, str | None]:
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            return None, erro
        if not eh_etf(simbolo_ok):
            return None, "O codigo informado nao consta como ETF no painel."

        codigo = simbolo_ok.replace(".SA", "")
        nome_etf = codigo
        aviso: str | None = None
        simbolo_consultado = simbolo_ok

        ativos, erro_busca = self._buscar_holdings_yahoo(simbolo_ok)
        if erro_busca or not ativos:
            proxy = obter_proxy_composicao(codigo)
            if proxy is None:
                return None, (
                    "Composicao da carteira indisponivel para este ETF no Yahoo Finance. "
                    "Consulte o site da gestora ou da B3 para a carteira oficial."
                )
            aviso = proxy.aviso
            simbolo_consultado = proxy.simbolo_yahoo
            ativos, erro_busca = self._buscar_holdings_yahoo(proxy.simbolo_yahoo)
            if erro_busca or not ativos:
                return None, (
                    "Nao foi possivel carregar a composicao de referencia. "
                    "Tente novamente em alguns minutos."
                )

        try:
            info = yf.Ticker(simbolo_ok).info or {}
            nome_etf = str(info.get("longName") or info.get("shortName") or codigo)
        except Exception:
            pass

        return (
            ComposicaoEtf(
                simbolo_etf=simbolo_ok,
                nome_etf=nome_etf,
                ativos=ativos,
                fonte="Yahoo Finance",
                aviso=aviso,
                simbolo_consultado=simbolo_consultado,
            ),
            None,
        )

    def _buscar_holdings_yahoo(
        self,
        simbolo: str,
    ) -> tuple[list[AtivoComposicaoEtf], str | None]:
        try:
            holdings = yf.Ticker(simbolo).funds_data.top_holdings
        except Exception as exc:
            self._log.aviso(f"Yahoo Finance (composicao ETF) falhou para {simbolo}: {exc}")
            return [], str(exc)

        if holdings is None or holdings.empty:
            return [], "Sem dados de carteira."

        ativos: list[AtivoComposicaoEtf] = []
        for simbolo_ativo, linha in holdings.iterrows():
            nome = str(linha.get("Name", "") or "").strip()
            percentual_bruto = linha.get("Holding Percent")
            if percentual_bruto is None:
                continue
            try:
                percentual = float(percentual_bruto) * 100.0
            except (TypeError, ValueError):
                continue
            codigo_exib = str(simbolo_ativo).replace(".SA", "").strip()
            if not codigo_exib:
                continue
            ativos.append(
                AtivoComposicaoEtf(
                    simbolo=codigo_exib,
                    nome=nome or codigo_exib,
                    percentual=percentual,
                )
            )

        if not ativos:
            return [], "Sem ativos na carteira retornada."

        ativos.sort(key=lambda item: item.percentual, reverse=True)
        return ativos, None
