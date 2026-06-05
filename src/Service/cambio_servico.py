"""Cotacao USD/BRL para exibir precos em real e dolar."""
from __future__ import annotations

import yfinance as yf

from src.Tool.registrador_log import RegistradorLog

_SIMBOLO_USD_BRL = "USDBRL=X"


class CambioServico:
    """Busca quantos reais custa 1 dolar americano (USDBRL=X)."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._taxa_em_cache: float | None = None

    def obter_taxa_usd_brl(self, usar_cache: bool = True) -> tuple[float | None, str | None]:
        """Retorna taxa BRL por 1 USD. Ex.: 5.12 significa US$ 1 = R$ 5,12."""
        if usar_cache and self._taxa_em_cache is not None and self._taxa_em_cache > 0:
            return self._taxa_em_cache, None

        try:
            dados = yf.download(
                _SIMBOLO_USD_BRL,
                period="5d",
                progress=False,
                auto_adjust=True,
            )
            if dados is not None and not dados.empty:
                coluna = dados["Close"]
                if hasattr(coluna, "columns"):
                    coluna = coluna.iloc[:, 0]
                taxa = float(coluna.dropna().iloc[-1])
                if taxa > 0:
                    self._taxa_em_cache = taxa
                    return taxa, None
        except Exception as exc:
            self._log.aviso(f"Cambio USD/BRL indisponivel: {exc}")

        return None, "Cambio USD/BRL indisponivel no momento."
