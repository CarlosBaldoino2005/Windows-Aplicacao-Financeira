"""Coleta informacoes fundamentais da acao via yfinance (sem API key)."""
from __future__ import annotations

import yfinance as yf

from src.Model.detalhes_acao import ConcorrenteResumo, DetalhesAcao
from src.Model.grupos_concorrentes import listar_codigos_concorrentes
from src.Tool.detalhes_financeiros_helper import (
    LINHAS_BALANCO,
    LINHAS_DRE,
    LINHAS_FLUXO,
    extrair_linhas_demonstrativo,
    extrair_periodos_resultado,
)
from src.Tool.registrador_log import RegistradorLog
from src.View.formatadores import formatar_moeda, formatar_numero_grande, formatar_percentual


class DetalhesAcaoServico:
    """Busca perfil da empresa, demonstrativos e concorrentes."""

    def __init__(self) -> None:
        self._log = RegistradorLog()

    def obter_detalhes(self, simbolo: str) -> tuple[DetalhesAcao | None, str | None]:
        try:
            ticker = yf.Ticker(simbolo)
            info = ticker.info or {}
        except Exception as exc:
            self._log.registrar_erro(f"Falha ao carregar detalhes de {simbolo}: {exc}")
            return None, "Nao foi possivel carregar os detalhes desta acao. Tente novamente."

        if not info or info.get("regularMarketPrice") is None and not info.get("longName"):
            return None, "Dados fundamentais indisponiveis para este codigo no Yahoo Finance."

        moeda = "BRL" if simbolo.endswith(".SA") else str(info.get("currency") or "USD")
        codigo = simbolo.replace(".SA", "")

        detalhes = DetalhesAcao(
            simbolo=simbolo,
            codigo=codigo,
            moeda=moeda,
            nome_empresa=str(info.get("longName") or info.get("shortName") or codigo),
            setor=str(info.get("sector") or ""),
            industria=str(info.get("industry") or ""),
            pais=str(info.get("country") or ""),
            site=str(info.get("website") or ""),
            descricao=str(info.get("longBusinessSummary") or "").strip(),
            funcionarios=_inteiro_opcional(info.get("fullTimeEmployees")),
            preco_atual=_float_opcional(info.get("regularMarketPrice") or info.get("currentPrice")),
            variacao_dia_pct=_float_opcional(info.get("regularMarketChangePercent")),
        )

        detalhes.indicadores = self._montar_indicadores(info, moeda)
        self._preencher_demonstrativos(ticker, detalhes)
        detalhes.concorrentes = self._buscar_concorrentes(
            simbolo,
            codigo,
            detalhes.industria,
            detalhes.setor,
        )

        if not detalhes.descricao:
            detalhes.avisos.append("Resumo da empresa nao disponivel na fonte de dados.")
        if not detalhes.trimestres and not detalhes.anuais:
            detalhes.avisos.append(
                "Demonstrativos trimestrais/anuais limitados para este ativo. "
                "Exibimos indicadores agregados quando existirem."
            )

        return detalhes, None

    def _montar_indicadores(self, info: dict, moeda: str) -> list[tuple[str, str]]:
        campos = [
            ("Preco atual", "regularMarketPrice", lambda v: formatar_moeda(float(v), moeda)),
            ("Capitalizacao", "marketCap", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Receita (TTM)", "totalRevenue", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Lucro liquido (TTM)", "netIncomeToCommon", lambda v: formatar_numero_grande(float(v), moeda)),
            ("EBITDA", "ebitda", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Margem de lucro", "profitMargins", formatar_percentual),
            ("Margem operacional", "operatingMargins", formatar_percentual),
            ("ROE", "returnOnEquity", formatar_percentual),
            ("P/L (trailing)", "trailingPE", lambda v: f"{float(v):.2f}"),
            ("P/L (forward)", "forwardPE", lambda v: f"{float(v):.2f}"),
            ("Dividend yield", "dividendYield", _formatar_dividend_yield),
            ("Beta", "beta", lambda v: f"{float(v):.2f}"),
            ("Divida/Patrimonio", "debtToEquity", lambda v: f"{float(v):.2f}"),
            ("Liquidez corrente", "currentRatio", lambda v: f"{float(v):.2f}"),
            ("Max. 52 semanas", "fiftyTwoWeekHigh", lambda v: formatar_moeda(float(v), moeda)),
            ("Min. 52 semanas", "fiftyTwoWeekLow", lambda v: formatar_moeda(float(v), moeda)),
            ("Recomendacao analistas", "recommendationKey", str),
            ("Opinioes de analistas", "numberOfAnalystOpinions", str),
            ("Setor", "sector", str),
            ("Industria", "industry", str),
            ("Funcionarios", "fullTimeEmployees", lambda v: f"{int(v):,}".replace(",", ".")),
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
            indicadores.append((rotulo, texto))

        return indicadores

    def _preencher_demonstrativos(self, ticker: yf.Ticker, detalhes: DetalhesAcao) -> None:
        try:
            q_dre = ticker.quarterly_income_stmt
            a_dre = ticker.income_stmt
            q_bal = ticker.quarterly_balance_sheet
            q_fluxo = ticker.quarterly_cashflow

            detalhes.trimestres = extrair_periodos_resultado(q_dre, maximo=8)
            detalhes.anuais = extrair_periodos_resultado(a_dre, maximo=6)
            detalhes.dre_trimestral = extrair_linhas_demonstrativo(q_dre, LINHAS_DRE)
            detalhes.dre_anual = extrair_linhas_demonstrativo(a_dre, LINHAS_DRE)
            detalhes.balanco = extrair_linhas_demonstrativo(q_bal, LINHAS_BALANCO)
            detalhes.fluxo_caixa = extrair_linhas_demonstrativo(q_fluxo, LINHAS_FLUXO)
        except Exception as exc:
            self._log.registrar_erro(f"Demonstrativos indisponiveis para {detalhes.simbolo}: {exc}")
            detalhes.avisos.append("Alguns demonstrativos financeiros nao puderam ser carregados.")

    def _buscar_concorrentes(
        self,
        simbolo_atual: str,
        codigo_atual: str,
        industria: str,
        setor: str,
    ) -> list[ConcorrenteResumo]:
        codigos = listar_codigos_concorrentes(industria, setor, codigo_atual, limite=8)
        if not codigos:
            return []

        concorrentes: list[ConcorrenteResumo] = []
        for codigo in codigos:
            simbolo = _simbolo_concorrente(codigo, simbolo_atual)
            if simbolo == simbolo_atual:
                continue

            try:
                info = yf.Ticker(simbolo).info or {}
            except Exception:
                continue

            if not info.get("longName") and not info.get("shortName"):
                continue

            moeda = "BRL" if simbolo.endswith(".SA") else str(info.get("currency") or "USD")
            concorrentes.append(
                ConcorrenteResumo(
                    codigo=codigo.replace(".SA", ""),
                    nome=str(info.get("shortName") or info.get("longName") or codigo),
                    moeda=moeda,
                    lucro_liquido=_float_opcional(info.get("netIncomeToCommon")),
                    margem_lucro=_float_opcional(info.get("profitMargins")),
                    receita=_float_opcional(info.get("totalRevenue")),
                    capitalizacao=_float_opcional(info.get("marketCap")),
                    preco_atual=_float_opcional(info.get("regularMarketPrice") or info.get("currentPrice")),
                    variacao_dia_pct=_float_opcional(info.get("regularMarketChangePercent")),
                )
            )

        concorrentes.sort(
            key=lambda item: item.capitalizacao or 0,
            reverse=True,
        )
        return concorrentes


def _formatar_dividend_yield(valor) -> str:
    """Yahoo pode retornar yield ja em percentual ou em decimal."""
    numero = float(valor)
    if abs(numero) > 1:
        return f"{numero:.2f}%"
    return formatar_percentual(numero)


def _simbolo_concorrente(codigo: str, referencia: str) -> str:
    """Mantem sufixo .SA quando a acao analisada e da B3."""
    limpo = codigo.replace(".SA", "")
    if referencia.endswith(".SA"):
        return f"{limpo}.SA"
    return limpo


def _float_opcional(valor) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _inteiro_opcional(valor) -> int | None:
    if valor is None:
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None
