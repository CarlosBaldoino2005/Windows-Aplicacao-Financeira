"""Detalhes da acao com fallback: Yahoo -> Brapi -> Yahoo Chart."""
from __future__ import annotations

import yfinance as yf

from src.Model.detalhes_acao import ConcorrenteResumo, DetalhesAcao
from src.Model.grupos_concorrentes import listar_codigos_concorrentes
from src.Service.provedores.cadeia_mercado import CadeiaMercado
from src.Service.provedores.provedor_brapi import ProvedorBrapi
from src.Service.provedores.provedor_yahoo_chart import ProvedorYahooChart
from src.Service.provedores.util_provedor import eh_acao_b3
from src.Tool.cadastro_empresa_helper import preencher_cadastro_empresa_de_yahoo
from src.Tool.dividendos_helper import extrair_pagamentos_dividendos
from src.Tool.detalhes_financeiros_helper import (
    LINHAS_BALANCO,
    LINHAS_DRE,
    LINHAS_FLUXO,
    extrair_linhas_demonstrativo,
    extrair_periodos_resultado,
)
from src.Tool.calculos_indicadores_helper import ContextoCalculoIndicador, montar_calculos_indicadores
from src.Tool.opinioes_analistas_helper import montar_opinioes_analistas, traduzir_nota_analista
from src.Tool.registrador_log import RegistradorLog
from src.View.formatadores import formatar_moeda, formatar_numero_grande, formatar_percentual


class DetalhesAcaoServico:
    """Busca perfil da empresa, demonstrativos e concorrentes com provedores de backup."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._cadeia = CadeiaMercado()
        self._brapi = ProvedorBrapi()
        self._yahoo_chart = ProvedorYahooChart()

    def obter_detalhes(self, simbolo: str) -> tuple[DetalhesAcao | None, str | None]:
        detalhes, fonte = self._tentar_yfinance(simbolo)
        if detalhes:
            detalhes.avisos.insert(0, f"Dados carregados via {fonte}.")
            return detalhes, None

        detalhes_backup, fonte_backup = self._tentar_backups(simbolo)
        if detalhes_backup:
            detalhes_backup.avisos.insert(
                0,
                f"Yahoo indisponivel. Dados basicos via {fonte_backup}. "
                "Demonstrativos completos podem estar limitados.",
            )
            return detalhes_backup, None

        return None, (
            "Nao foi possivel carregar detalhes (Yahoo, Brapi e Yahoo Chart indisponiveis). "
            "Tente novamente em alguns minutos."
        )

    def _tentar_yfinance(self, simbolo: str) -> tuple[DetalhesAcao | None, str]:
        try:
            ticker = yf.Ticker(simbolo)
            info = ticker.info or {}
        except Exception as exc:
            self._log.aviso(f"Yahoo Finance (detalhes) falhou para {simbolo}: {exc}")
            return None, ""

        if not info or (info.get("regularMarketPrice") is None and not info.get("longName")):
            return None, ""

        detalhes = self._montar_de_info_yahoo(simbolo, info)
        self._preencher_demonstrativos_yfinance(ticker, detalhes)
        self._preencher_dividendos_pagos(simbolo, detalhes)
        self._preencher_opinioes_analistas(ticker, detalhes)
        self._preencher_calculos_indicadores(detalhes, info)  # apos dividendos (ultimo dividendo)
        detalhes.concorrentes = self._buscar_concorrentes(
            simbolo,
            detalhes.codigo,
            detalhes.industria,
            detalhes.setor,
        )
        self._complementar_avisos(detalhes)
        return detalhes, "Yahoo Finance"

    def _tentar_backups(self, simbolo: str) -> tuple[DetalhesAcao | None, str]:
        if eh_acao_b3(simbolo):
            detalhes, info_fonte = self._montar_de_brapi(simbolo)
            if detalhes:
                self._preencher_dividendos_pagos(simbolo, detalhes)
                self._preencher_calculos_indicadores(
                    detalhes,
                    info_fonte,
                    ContextoCalculoIndicador(
                        preco=detalhes.preco_atual,
                        variacao_pct=detalhes.variacao_dia_pct,
                    ),
                )
                return detalhes, "Brapi"

        detalhes, info_fonte, contexto_fonte = self._montar_de_yahoo_chart(simbolo)
        if detalhes:
            self._preencher_dividendos_pagos(simbolo, detalhes)
            self._preencher_calculos_indicadores(detalhes, info_fonte, contexto_fonte)
            return detalhes, "Yahoo Chart API"

        return None, ""

    def _montar_de_info_yahoo(self, simbolo: str, info: dict) -> DetalhesAcao:
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
        preencher_cadastro_empresa_de_yahoo(detalhes, info)
        return detalhes

    def _montar_de_brapi(self, simbolo: str) -> tuple[DetalhesAcao | None, dict]:
        dados = self._brapi.buscar_cotacao_detalhe(simbolo)
        if not dados or not dados.get("results"):
            return None, {}

        item = dados["results"][0]
        codigo = simbolo.replace(".SA", "")
        moeda = str(item.get("currency") or "BRL")
        preco = _float_opcional(item.get("regularMarketPrice"))
        variacao_pct = _float_opcional(item.get("regularMarketChangePercent"))

        detalhes = DetalhesAcao(
            simbolo=simbolo,
            codigo=codigo,
            moeda=moeda,
            nome_empresa=str(item.get("longName") or item.get("shortName") or codigo),
            setor="",
            industria="",
            pais="Brasil",
            site="",
            descricao="",
            preco_atual=preco,
            variacao_dia_pct=variacao_pct,
        )

        indicadores: list[tuple[str, str]] = []
        if preco is not None:
            indicadores.append(("Preco atual", formatar_moeda(preco, moeda)))
        if item.get("marketCap"):
            indicadores.append(("Capitalizacao", formatar_numero_grande(float(item["marketCap"]), moeda)))
        if item.get("priceEarnings"):
            indicadores.append(("P/L", f"{float(item['priceEarnings']):.2f}"))
        texto_p_vpa = _formatar_p_vpa(item, preco)
        if texto_p_vpa:
            indicadores.append(("P/VPA", texto_p_vpa))
        vpa = _float_opcional(item.get("bookValue"))
        if vpa is not None:
            indicadores.append(("VPA", formatar_moeda(vpa, moeda)))
        if item.get("earningsPerShare"):
            indicadores.append(("Lucro por acao", formatar_moeda(float(item["earningsPerShare"]), moeda)))
        if variacao_pct is not None:
            indicadores.append(("Variacao do dia", f"{variacao_pct:.2f}%"))

        faixa = item.get("fiftyTwoWeekRange") or item.get("regularMarketDayRange")
        if faixa:
            indicadores.append(("Faixa de preco (dia/52s)", str(faixa)))

        detalhes.indicadores = indicadores
        detalhes.concorrentes = self._buscar_concorrentes(simbolo, codigo, detalhes.industria, detalhes.setor)
        self._complementar_avisos(detalhes)
        return detalhes, item

    def _montar_de_yahoo_chart(
        self,
        simbolo: str,
    ) -> tuple[DetalhesAcao | None, dict, ContextoCalculoIndicador | None]:
        meta = self._yahoo_chart.buscar_meta(simbolo)
        resumo = self._cadeia.buscar_resumos([simbolo])
        if not meta and not resumo:
            return None, {}, None

        codigo = simbolo.replace(".SA", "")
        moeda = "BRL" if simbolo.endswith(".SA") else "USD"
        nome = codigo
        preco = None
        variacao_pct = None
        preco_anterior = None

        if meta:
            moeda = str(meta.get("currency") or moeda)
            nome = str(meta.get("longName") or meta.get("shortName") or codigo)
            preco = _float_opcional(meta.get("regularMarketPrice"))
            preco_anterior = _float_opcional(meta.get("chartPreviousClose") or meta.get("previousClose"))
            if preco is not None and preco_anterior:
                variacao_pct = round(((preco - preco_anterior) / preco_anterior) * 100, 2)

        if resumo:
            item = resumo[0]
            nome = item.nome or nome
            preco = item.preco
            variacao_pct = item.variacao_percentual
            moeda = item.moeda

        detalhes = DetalhesAcao(
            simbolo=simbolo,
            codigo=codigo,
            moeda=moeda,
            nome_empresa=nome,
            preco_atual=preco,
            variacao_dia_pct=variacao_pct,
        )
        if preco is not None:
            detalhes.indicadores = [("Preco atual", formatar_moeda(preco, moeda))]
            if variacao_pct is not None:
                detalhes.indicadores.append(("Variacao do dia", f"{variacao_pct:.2f}%"))

        contexto = ContextoCalculoIndicador(
            preco=preco,
            variacao_pct=variacao_pct,
            preco_anterior=preco_anterior,
        )
        detalhes.concorrentes = self._buscar_concorrentes(simbolo, codigo, detalhes.industria, detalhes.setor)
        self._complementar_avisos(detalhes)
        return detalhes, meta or {}, contexto

    def _montar_indicadores(self, info: dict, moeda: str) -> list[tuple[str, str]]:
        campos = [
            ("Preco atual", "regularMarketPrice", lambda v: formatar_moeda(float(v), moeda)),
            ("Variacao do dia", "regularMarketChangePercent", lambda v: f"{float(v):.2f}%"),
            ("Capitalizacao", "marketCap", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Valor da empresa", "enterpriseValue", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Receita (TTM)", "totalRevenue", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Lucro liquido (TTM)", "netIncomeToCommon", lambda v: formatar_numero_grande(float(v), moeda)),
            ("EBITDA", "ebitda", lambda v: formatar_numero_grande(float(v), moeda)),
            ("Margem bruta", "grossMargins", formatar_percentual),
            ("Margem de lucro", "profitMargins", formatar_percentual),
            ("Margem operacional", "operatingMargins", formatar_percentual),
            ("ROE", "returnOnEquity", formatar_percentual),
            ("ROA", "returnOnAssets", formatar_percentual),
            ("P/L (trailing)", "trailingPE", lambda v: f"{float(v):.2f}"),
            ("P/L (forward)", "forwardPE", lambda v: f"{float(v):.2f}"),
            ("Lucro por acao", "trailingEps", lambda v: formatar_moeda(float(v), moeda)),
            ("P/Vendas", "priceToSalesTrailing12Months", lambda v: f"{float(v):.2f}"),
            ("PEG", "pegRatio", lambda v: f"{float(v):.2f}"),
            ("Dividend yield", "dividendYield", _formatar_dividend_yield),
            ("Payout dividendos", "payoutRatio", formatar_percentual),
            ("Beta", "beta", lambda v: f"{float(v):.2f}"),
            ("Divida/Patrimonio", "debtToEquity", lambda v: f"{float(v):.2f}"),
            ("Liquidez corrente", "currentRatio", lambda v: f"{float(v):.2f}"),
            ("Liquidez seca", "quickRatio", lambda v: f"{float(v):.2f}"),
            ("Variacao 52 semanas", "52WeekChange", formatar_percentual),
            ("Volume do dia", "regularMarketVolume", _formatar_quantidade_grande),
            ("Volume medio", "averageVolume", _formatar_quantidade_grande),
            ("Max. 52 semanas", "fiftyTwoWeekHigh", lambda v: formatar_moeda(float(v), moeda)),
            ("Min. 52 semanas", "fiftyTwoWeekLow", lambda v: formatar_moeda(float(v), moeda)),
            ("Preco alvo medio", "targetMeanPrice", lambda v: formatar_moeda(float(v), moeda)),
            ("Recomendacao analistas", "recommendationKey", traduzir_nota_analista),
            ("Opinioes de analistas", "numberOfAnalystOpinions", str),
            ("Acoes em circulacao", "sharesOutstanding", _formatar_quantidade_grande),
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

        texto_p_vpa = _formatar_p_vpa(
            info,
            _float_opcional(info.get("regularMarketPrice") or info.get("currentPrice")),
        )
        if texto_p_vpa:
            if any(rotulo == "P/L (forward)" for rotulo, _ in indicadores):
                _inserir_indicador_apos(indicadores, "P/L (forward)", ("P/VPA", texto_p_vpa))
            elif any(rotulo == "P/L (trailing)" for rotulo, _ in indicadores):
                _inserir_indicador_apos(indicadores, "P/L (trailing)", ("P/VPA", texto_p_vpa))
            else:
                indicadores.append(("P/VPA", texto_p_vpa))

        vpa = _float_opcional(info.get("bookValue"))
        if vpa is not None:
            if any(rotulo == "P/VPA" for rotulo, _ in indicadores):
                _inserir_indicador_apos(indicadores, "P/VPA", ("VPA", formatar_moeda(vpa, moeda)))
            else:
                indicadores.append(("VPA", formatar_moeda(vpa, moeda)))

        return indicadores

    def _preencher_calculos_indicadores(
        self,
        detalhes: DetalhesAcao,
        info: dict,
        contexto: ContextoCalculoIndicador | None = None,
    ) -> None:
        rotulos = {rotulo for rotulo, _ in detalhes.indicadores}
        if not rotulos:
            detalhes.calculos_indicadores = {}
            return

        ctx = contexto or ContextoCalculoIndicador(
            preco=detalhes.preco_atual,
            variacao_pct=detalhes.variacao_dia_pct,
        )
        if detalhes.pagamentos_dividendos:
            ultimo = detalhes.pagamentos_dividendos[0]
            ctx.ultimo_dividendo_valor = ultimo.valor_por_cota
            ctx.ultimo_dividendo_data = ultimo.data_pagamento

        detalhes.calculos_indicadores = montar_calculos_indicadores(
            info,
            detalhes.moeda,
            rotulos,
            ctx,
        )

    def _preencher_opinioes_analistas(self, ticker, detalhes: DetalhesAcao) -> None:
        if detalhes.eh_cripto:
            return
        try:
            detalhes.opinioes_analistas = montar_opinioes_analistas(
                detalhes.simbolo,
                detalhes.nome_empresa,
                detalhes.moeda,
                ticker=ticker,
            )
        except Exception as exc:
            self._log.aviso(f"Opinioes de analistas indisponiveis para {detalhes.simbolo}: {exc}")

    def _preencher_dividendos_pagos(self, simbolo: str, detalhes: DetalhesAcao) -> None:
        if simbolo.endswith("-USD"):
            return
        detalhes.pagamentos_dividendos = extrair_pagamentos_dividendos(simbolo)
        if detalhes.pagamentos_dividendos:
            ultimo = detalhes.pagamentos_dividendos[0]
            detalhes.indicadores.insert(
                0,
                (
                    "Ultimo dividendo pago",
                    f"{ultimo.data_pagamento} — {formatar_moeda(ultimo.valor_por_cota, detalhes.moeda)}",
                ),
            )
        else:
            detalhes.avisos.append(
                "Historico de dividendos pagos nao disponivel na fonte para esta acao."
            )

    def _preencher_demonstrativos_yfinance(self, ticker: yf.Ticker, detalhes: DetalhesAcao) -> None:
        try:
            detalhes.trimestres = extrair_periodos_resultado(ticker.quarterly_income_stmt, maximo=8)
            detalhes.anuais = extrair_periodos_resultado(ticker.income_stmt, maximo=6)
            detalhes.dre_trimestral = extrair_linhas_demonstrativo(ticker.quarterly_income_stmt, LINHAS_DRE)
            detalhes.dre_anual = extrair_linhas_demonstrativo(ticker.income_stmt, LINHAS_DRE)
            detalhes.balanco = extrair_linhas_demonstrativo(ticker.quarterly_balance_sheet, LINHAS_BALANCO)
            detalhes.fluxo_caixa = extrair_linhas_demonstrativo(ticker.quarterly_cashflow, LINHAS_FLUXO)
        except Exception as exc:
            self._log.aviso(f"Demonstrativos Yahoo indisponiveis para {detalhes.simbolo}: {exc}")
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

        simbolos = [_simbolo_concorrente(c, simbolo_atual) for c in codigos]
        simbolos = [s for s in simbolos if s != simbolo_atual]
        resumos = self._cadeia.buscar_resumos(simbolos)

        concorrentes: list[ConcorrenteResumo] = []
        for item in resumos:
            concorrentes.append(
                ConcorrenteResumo(
                    codigo=item.simbolo.replace(".SA", ""),
                    nome=item.nome,
                    moeda=item.moeda,
                    preco_atual=item.preco,
                    variacao_dia_pct=item.variacao_percentual,
                    lucro_liquido=None,
                    margem_lucro=None,
                    receita=None,
                    capitalizacao=None,
                )
            )

        concorrentes.sort(key=lambda c: c.preco_atual or 0, reverse=True)
        return concorrentes

    @staticmethod
    def _complementar_avisos(detalhes: DetalhesAcao) -> None:
        if not detalhes.descricao:
            detalhes.avisos.append("Resumo da empresa nao disponivel na fonte de dados.")
        if not detalhes.trimestres and not detalhes.anuais:
            detalhes.avisos.append(
                "Demonstrativos trimestrais/anuais limitados para este ativo. "
                "Exibimos indicadores agregados quando existirem."
            )


def _formatar_p_vpa(info: dict, preco: float | None = None) -> str | None:
    """Preco sobre valor patrimonial por acao (P/VPA), via Yahoo ou preco / VPA."""
    valor = info.get("priceToBook")
    if valor is not None and valor != "":
        try:
            return f"{float(valor):.2f}"
        except (TypeError, ValueError):
            pass

    vpa = _float_opcional(info.get("bookValue"))
    preco_calc = preco if preco is not None else _float_opcional(
        info.get("regularMarketPrice") or info.get("currentPrice")
    )
    if preco_calc is not None and vpa is not None and vpa != 0:
        return f"{preco_calc / vpa:.2f}"
    return None


def _inserir_indicador_apos(
    indicadores: list[tuple[str, str]],
    rotulo_referencia: str,
    novo: tuple[str, str],
) -> None:
    for indice, (rotulo, _) in enumerate(indicadores):
        if rotulo == rotulo_referencia:
            indicadores.insert(indice + 1, novo)
            return


def _formatar_quantidade_grande(valor) -> str:
    """Formata volume ou quantidade de papeis para exibicao em pt-BR."""
    try:
        numero = int(float(valor))
    except (TypeError, ValueError):
        return str(valor)
    return f"{numero:,}".replace(",", ".")


def _formatar_dividend_yield(valor) -> str:
    numero = float(valor)
    if abs(numero) > 1:
        return f"{numero:.2f}%"
    return formatar_percentual(numero)


def _simbolo_concorrente(codigo: str, referencia: str) -> str:
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