"""Detalhes de criptomoeda via Yahoo Finance (Ticker.info)."""
from __future__ import annotations

from datetime import datetime

from collections.abc import Callable

import yfinance as yf

from src.Model.cripto_universo import CRIPTOMOEDAS_MONITORADAS, NOMES_CRIPTO
from src.Model.detalhes_acao import ConcorrenteResumo, DetalhesAcao
from src.Service.mercado_cripto_servico import MercadoCriptoServico
from src.Tool.registrador_log import RegistradorLog
from src.View.formatadores import formatar_moeda, formatar_numero_grande, formatar_percentual


class DetalhesCriptoServico:
    """Monta pacote DetalhesAcao com indicadores e pares do mercado cripto."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._mercado = MercadoCriptoServico()

    def obter_detalhes(self, simbolo: str) -> tuple[DetalhesAcao | None, str | None]:
        try:
            ticker = yf.Ticker(simbolo)
            info = ticker.info or {}
        except Exception as exc:
            self._log.aviso(f"Yahoo Finance (detalhes cripto) falhou para {simbolo}: {exc}")
            return None, (
                "Nao foi possivel carregar detalhes da criptomoeda. "
                "Tente novamente em alguns minutos."
            )

        if not info or info.get("regularMarketPrice") is None and not info.get("longName"):
            return None, "Detalhes indisponiveis para este codigo de criptomoeda."

        detalhes = self._montar_de_info(simbolo, info)
        detalhes.concorrentes = self._buscar_outras_criptos(simbolo)
        detalhes.avisos.insert(0, "Dados carregados via Yahoo Finance.")
        if not detalhes.descricao:
            detalhes.avisos.append("Descricao do ativo nao disponivel na fonte de dados.")
        return detalhes, None

    def _montar_de_info(self, simbolo: str, info: dict) -> DetalhesAcao:
        moeda = str(info.get("currency") or "USD")
        codigo = simbolo.replace("-USD", "")
        nome = str(info.get("longName") or info.get("shortName") or NOMES_CRIPTO.get(simbolo, codigo))

        detalhes = DetalhesAcao(
            simbolo=simbolo,
            codigo=codigo,
            moeda=moeda,
            nome_empresa=nome,
            setor=str(info.get("category") or "Criptomoeda"),
            industria=str(info.get("quoteType") or "CRYPTOCURRENCY"),
            pais="",
            site=_extrair_site_da_descricao(info),
            descricao=str(info.get("description") or "").strip(),
            preco_atual=_float_opcional(info.get("regularMarketPrice") or info.get("currentPrice")),
            variacao_dia_pct=_float_opcional(info.get("regularMarketChangePercent")),
            indicadores=self._montar_indicadores(info, moeda),
            eh_cripto=True,
        )
        return detalhes

    def _montar_indicadores(self, info: dict, moeda: str) -> list[tuple[str, str]]:
        campos: list[tuple[str, str, Callable[[object], str]]] = [
            ("Preco atual", "regularMarketPrice", lambda v: formatar_moeda(float(v), moeda)),
            ("Variacao do dia", "regularMarketChangePercent", lambda v: f"{float(v):.2f}%"),
            ("Capitalizacao de mercado", "marketCap", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Volume 24h", "volume24Hr", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Volume (todas moedas)", "volumeAllCurrencies", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Oferta em circulacao", "circulatingSupply", _formatar_quantidade),
            ("Oferta maxima", "maxSupply", _formatar_quantidade),
            ("Max. 52 semanas", "fiftyTwoWeekHigh", lambda v: formatar_moeda(float(v), moeda)),
            ("Min. 52 semanas", "fiftyTwoWeekLow", lambda v: formatar_moeda(float(v), moeda)),
            ("Maximo historico", "allTimeHigh", lambda v: formatar_moeda(float(v), moeda)),
            ("Minimo historico", "allTimeLow", lambda v: formatar_moeda(float(v), moeda)),
            ("Media volume (10 dias)", "averageVolume10days", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Media volume", "averageVolume", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Variacao 52 semanas", "52WeekChange", lambda v: formatar_percentual(float(v))),
            ("Preco de abertura", "regularMarketOpen", lambda v: formatar_moeda(float(v), moeda)),
            ("Preco anterior", "regularMarketPreviousClose", lambda v: formatar_moeda(float(v), moeda)),
            ("Algoritmo", "algorithm", str),
            ("Moeda base", "fromCurrency", str),
            ("Data de lancamento", "startDate", _formatar_data_unix),
        ]

        indicadores: list[tuple[str, str]] = []
        for rotulo, chave, formatador in campos:
            valor = info.get(chave)
            if valor is None or valor == "":
                continue
            try:
                texto = formatador(valor)
            except (TypeError, ValueError):
                texto = str(valor)
            if texto and texto.strip():
                indicadores.append((rotulo, texto))
        return indicadores

    def _buscar_outras_criptos(self, simbolo_atual: str) -> list[ConcorrenteResumo]:
        outros = [s for s in CRIPTOMOEDAS_MONITORADAS if s != simbolo_atual][:12]
        if not outros:
            return []

        resumos = self._mercado.buscar_resumos(outros)
        pares: list[ConcorrenteResumo] = []
        for item in resumos:
            pares.append(
                ConcorrenteResumo(
                    codigo=item.simbolo.replace("-USD", ""),
                    nome=item.nome,
                    moeda=item.moeda,
                    preco_atual=item.preco,
                    variacao_dia_pct=item.variacao_percentual,
                    capitalizacao=None,
                )
            )

        pares.sort(key=lambda p: p.preco_atual or 0, reverse=True)
        return pares[:8]


def _extrair_site_da_descricao(info: dict) -> str:
    descricao = str(info.get("description") or "")
    if "http://" in descricao or "https://" in descricao:
        for parte in descricao.replace(")", " ").replace("(", " ").split():
            if parte.startswith("http://") or parte.startswith("https://"):
                return parte.rstrip(".,;")
    return ""


def _formatar_quantidade(valor) -> str:
    numero = float(valor)
    texto = f"{numero:,.0f}" if numero >= 1 else f"{numero:.8f}".rstrip("0")
    return texto.replace(",", ".")


def _formatar_data_unix(valor) -> str:
    try:
        timestamp = float(valor)
        if timestamp > 1e12:
            timestamp /= 1000
        return datetime.utcfromtimestamp(timestamp).strftime("%d/%m/%Y")
    except (TypeError, ValueError, OSError):
        return str(valor)


def _float_opcional(valor) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None
