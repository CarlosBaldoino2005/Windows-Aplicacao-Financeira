"""Monta formula, valores e passos de calculo para indicadores com conta."""
from __future__ import annotations

from dataclasses import dataclass

from src.View.formatadores import formatar_moeda, formatar_numero_grande, formatar_percentual


@dataclass
class ContextoCalculoIndicador:
    """Valores extras quando a fonte nao entrega o dicionario completo do Yahoo."""

    preco: float | None = None
    variacao_pct: float | None = None
    preco_anterior: float | None = None
    ultimo_dividendo_valor: float | None = None
    ultimo_dividendo_data: str | None = None


def _float_opcional(valor) -> float | None:
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _preco_info(info: dict, contexto: ContextoCalculoIndicador | None) -> float | None:
    if contexto and contexto.preco is not None:
        return contexto.preco
    return _float_opcional(info.get("regularMarketPrice") or info.get("currentPrice"))


def _linha_calculo(formula: str, partes: list[tuple[str, str]], resultado: str) -> str:
    linhas = [f"Formula: {formula}", ""]
    for rotulo, valor in partes:
        linhas.append(f"{rotulo}: {valor}")
    linhas.extend(["", f"Resultado: {resultado}"])
    return "\n".join(linhas)


def _calculo_p_vpa(info: dict, moeda: str, contexto: ContextoCalculoIndicador | None) -> str | None:
    preco = _preco_info(info, contexto)
    vpa = _float_opcional(info.get("bookValue"))
    price_to_book = _float_opcional(info.get("priceToBook"))

    if price_to_book is not None:
        partes: list[tuple[str, str]] = [
            ("P/VPA (fonte Yahoo)", f"{price_to_book:.2f}"),
        ]
        if preco is not None:
            partes.append(("Preco da acao", formatar_moeda(preco, moeda)))
        if vpa is not None:
            partes.append(("VPA", formatar_moeda(vpa, moeda)))
        resultado = f"{price_to_book:.2f}"
        if preco is not None and vpa is not None and vpa != 0:
            resultado = f"{formatar_moeda(preco, moeda)} / {vpa:.4f} = {preco / vpa:.2f}"
        return _linha_calculo("P/VPA = Preco da acao / VPA", partes, resultado)

    if preco is not None and vpa is not None and vpa != 0:
        resultado = preco / vpa
        return _linha_calculo(
            "P/VPA = Preco da acao / VPA",
            [
                ("Preco da acao", formatar_moeda(preco, moeda)),
                ("VPA", formatar_moeda(vpa, moeda)),
            ],
            f"{formatar_moeda(preco, moeda)} / {vpa:.4f} = {resultado:.2f}",
        )
    return None


def _calculo_vpa(info: dict, moeda: str) -> str | None:
    vpa = _float_opcional(info.get("bookValue"))
    if vpa is None:
        return None

    patrimonio = _float_opcional(info.get("totalStockholderEquity"))
    acoes = _float_opcional(info.get("sharesOutstanding"))
    partes = [("VPA informado pela fonte", formatar_moeda(vpa, moeda))]
    if patrimonio is not None and acoes is not None and acoes != 0:
        calculado = patrimonio / acoes
        return _linha_calculo(
            "VPA = Patrimonio liquido / Acoes em circulacao",
            [
                ("Patrimonio liquido", formatar_numero_grande(patrimonio, moeda)),
                ("Acoes em circulacao", f"{int(acoes):,}".replace(",", ".")),
            ],
            f"{formatar_numero_grande(patrimonio, moeda)} / {acoes:,.0f} = {formatar_moeda(calculado, moeda)}",
        )
    return _linha_calculo(
        "VPA = Valor patrimonial por acao",
        partes,
        formatar_moeda(vpa, moeda),
    )


def _calculo_p_l(
    info: dict,
    moeda: str,
    contexto: ContextoCalculoIndicador | None,
    chave_pe: str,
    chave_eps: str,
    rotulo_pe: str,
) -> str | None:
    preco = _preco_info(info, contexto)
    pe = _float_opcional(info.get(chave_pe))
    eps = _float_opcional(info.get(chave_eps))

    if pe is not None:
        partes: list[tuple[str, str]] = [(rotulo_pe, f"{pe:.2f}")]
        if preco is not None:
            partes.append(("Preco da acao", formatar_moeda(preco, moeda)))
        if eps is not None:
            partes.append(("Lucro por acao", formatar_moeda(eps, moeda)))
        resultado = f"{pe:.2f}"
        if preco is not None and eps is not None and eps != 0:
            resultado = f"{formatar_moeda(preco, moeda)} / {eps:.4f} = {preco / eps:.2f}"
        return _linha_calculo("P/L = Preco da acao / Lucro por acao", partes, resultado)

    if preco is not None and eps is not None and eps != 0:
        resultado = preco / eps
        return _linha_calculo(
            "P/L = Preco da acao / Lucro por acao",
            [
                ("Preco da acao", formatar_moeda(preco, moeda)),
                ("Lucro por acao", formatar_moeda(eps, moeda)),
            ],
            f"{formatar_moeda(preco, moeda)} / {eps:.4f} = {resultado:.2f}",
        )
    return None


def _calculo_p_vendas(info: dict, moeda: str, contexto: ContextoCalculoIndicador | None) -> str | None:
    preco = _preco_info(info, contexto)
    p_vendas = _float_opcional(info.get("priceToSalesTrailing12Months"))
    receita = _float_opcional(info.get("totalRevenue"))
    acoes = _float_opcional(info.get("sharesOutstanding"))

    if p_vendas is not None:
        partes: list[tuple[str, str]] = [("P/Vendas (fonte Yahoo)", f"{p_vendas:.2f}")]
        if preco is not None:
            partes.append(("Preco da acao", formatar_moeda(preco, moeda)))
        if receita is not None and acoes is not None and acoes != 0:
            receita_por_acao = receita / acoes
            partes.append(("Receita por acao (TTM)", formatar_moeda(receita_por_acao, moeda)))
        return _linha_calculo("P/Vendas = Preco da acao / Receita por acao", partes, f"{p_vendas:.2f}")

    if preco is not None and receita is not None and acoes is not None and acoes != 0:
        receita_por_acao = receita / acoes
        if receita_por_acao == 0:
            return None
        resultado = preco / receita_por_acao
        return _linha_calculo(
            "P/Vendas = Preco da acao / Receita por acao",
            [
                ("Preco da acao", formatar_moeda(preco, moeda)),
                ("Receita (TTM)", formatar_numero_grande(receita, moeda)),
                ("Acoes em circulacao", f"{int(acoes):,}".replace(",", ".")),
                ("Receita por acao", formatar_moeda(receita_por_acao, moeda)),
            ],
            f"{formatar_moeda(preco, moeda)} / {receita_por_acao:.4f} = {resultado:.2f}",
        )
    return None


def _calculo_lucro_por_acao(info: dict, moeda: str) -> str | None:
    eps = _float_opcional(info.get("trailingEps") or info.get("earningsPerShare"))
    lucro = _float_opcional(info.get("netIncomeToCommon"))
    acoes = _float_opcional(info.get("sharesOutstanding"))

    if eps is not None and lucro is not None and acoes is not None and acoes != 0:
        calculado = lucro / acoes
        return _linha_calculo(
            "Lucro por acao = Lucro liquido (TTM) / Acoes em circulacao",
            [
                ("Lucro liquido (TTM)", formatar_numero_grande(lucro, moeda)),
                ("Acoes em circulacao", f"{int(acoes):,}".replace(",", ".")),
            ],
            f"{formatar_numero_grande(lucro, moeda)} / {acoes:,.0f} = {formatar_moeda(calculado, moeda)}",
        )

    if eps is not None:
        return _linha_calculo(
            "Lucro por acao = Lucro liquido / Acoes em circulacao",
            [("Lucro por acao (fonte Yahoo)", formatar_moeda(eps, moeda))],
            formatar_moeda(eps, moeda),
        )
    return None


def _calculo_dividend_yield(info: dict, moeda: str, contexto: ContextoCalculoIndicador | None) -> str | None:
    preco = _preco_info(info, contexto)
    taxa = _float_opcional(info.get("dividendYield"))
    dividendo_anual = _float_opcional(info.get("dividendRate") or info.get("trailingAnnualDividendRate"))

    if taxa is None:
        return None

    taxa_exibicao = taxa * 100 if abs(taxa) <= 1 else taxa
    partes: list[tuple[str, str]] = []
    if preco is not None:
        partes.append(("Preco da acao", formatar_moeda(preco, moeda)))
    if dividendo_anual is not None:
        partes.append(("Dividendo anual por acao", formatar_moeda(dividendo_anual, moeda)))

    if preco is not None and dividendo_anual is not None and preco != 0:
        calculado = (dividendo_anual / preco) * 100
        return _linha_calculo(
            "Dividend yield = (Dividendo anual por acao / Preco da acao) x 100",
            partes,
            f"({formatar_moeda(dividendo_anual, moeda)} / {preco:.4f}) x 100 = {calculado:.2f}%",
        )

    return _linha_calculo(
        "Dividend yield = (Dividendo anual / Preco) x 100",
        partes or [("Taxa informada pela fonte", f"{taxa_exibicao:.2f}%")],
        f"{taxa_exibicao:.2f}%",
    )


def _calculo_margem(
    info: dict,
    moeda: str,
    chave_margem: str,
    nome_margem: str,
    chave_lucro: str | None,
) -> str | None:
    margem = _float_opcional(info.get(chave_margem))
    receita = _float_opcional(info.get("totalRevenue"))
    if margem is None:
        return None

    texto_margem = formatar_percentual(margem)
    partes: list[tuple[str, str]] = [(nome_margem, texto_margem)]
    if receita is not None:
        partes.append(("Receita (TTM)", formatar_numero_grande(receita, moeda)))

    if chave_lucro and receita is not None:
        lucro = _float_opcional(info.get(chave_lucro))
        if lucro is not None and receita != 0:
            calculado = lucro / receita
            return _linha_calculo(
                f"{nome_margem} = (Componente do lucro / Receita) x 100",
                [
                    ("Receita (TTM)", formatar_numero_grande(receita, moeda)),
                    ("Componente usado", formatar_numero_grande(lucro, moeda)),
                ],
                f"({formatar_numero_grande(lucro, moeda)} / {formatar_numero_grande(receita, moeda)}) x 100 = {formatar_percentual(calculado)}",
            )

    return _linha_calculo(
        f"{nome_margem} = percentual sobre a receita",
        partes,
        texto_margem,
    )


def _calculo_capitalizacao(info: dict, moeda: str, contexto: ContextoCalculoIndicador | None) -> str | None:
    cap = _float_opcional(info.get("marketCap"))
    preco = _preco_info(info, contexto)
    acoes = _float_opcional(info.get("sharesOutstanding"))
    if cap is None:
        return None

    if preco is not None and acoes is not None:
        calculado = preco * acoes
        return _linha_calculo(
            "Capitalizacao = Preco da acao x Acoes em circulacao",
            [
                ("Preco da acao", formatar_moeda(preco, moeda)),
                ("Acoes em circulacao", f"{int(acoes):,}".replace(",", ".")),
            ],
            f"{formatar_moeda(preco, moeda)} x {acoes:,.0f} = {formatar_numero_grande(calculado, moeda)}",
        )

    return _linha_calculo(
        "Capitalizacao = Preco x Acoes em circulacao",
        [("Valor informado pela fonte", formatar_numero_grande(cap, moeda))],
        formatar_numero_grande(cap, moeda),
    )


def _calculo_variacao_dia(
    info: dict,
    moeda: str,
    contexto: ContextoCalculoIndicador | None,
) -> str | None:
    if contexto and contexto.variacao_pct is not None and contexto.preco_anterior is not None and contexto.preco:
        anterior = contexto.preco_anterior
        preco = contexto.preco
        variacao = contexto.variacao_pct
        return _linha_calculo(
            "Variacao do dia = ((Preco atual - Fechamento anterior) / Fechamento anterior) x 100",
            [
                ("Preco atual", formatar_moeda(preco, moeda)),
                ("Fechamento anterior", formatar_moeda(anterior, moeda)),
            ],
            f"(({preco:.4f} - {anterior:.4f}) / {anterior:.4f}) x 100 = {variacao:.2f}%",
        )

    variacao = _float_opcional(info.get("regularMarketChangePercent"))
    preco = _preco_info(info, contexto)
    anterior = _float_opcional(info.get("previousClose") or info.get("regularMarketPreviousClose"))
    if variacao is None:
        return None

    partes: list[tuple[str, str]] = [("Variacao informada pela fonte", f"{variacao:.2f}%")]
    if preco is not None:
        partes.append(("Preco atual", formatar_moeda(preco, moeda)))
    if anterior is not None:
        partes.append(("Fechamento anterior", formatar_moeda(anterior, moeda)))

    if preco is not None and anterior is not None and anterior != 0:
        calculado = ((preco - anterior) / anterior) * 100
        return _linha_calculo(
            "Variacao do dia = ((Preco atual - Fechamento anterior) / Fechamento anterior) x 100",
            [
                ("Preco atual", formatar_moeda(preco, moeda)),
                ("Fechamento anterior", formatar_moeda(anterior, moeda)),
            ],
            f"(({preco:.4f} - {anterior:.4f}) / {anterior:.4f}) x 100 = {calculado:.2f}%",
        )

    return _linha_calculo(
        "Variacao do dia = variacao percentual em relacao ao fechamento anterior",
        partes,
        f"{variacao:.2f}%",
    )


def _calculo_peg(info: dict) -> str | None:
    peg = _float_opcional(info.get("pegRatio"))
    if peg is None:
        return None
    pe = _float_opcional(info.get("trailingPE"))
    partes: list[tuple[str, str]] = [("PEG (fonte Yahoo)", f"{peg:.2f}")]
    if pe is not None:
        partes.append(("P/L trailing", f"{pe:.2f}"))
    return _linha_calculo("PEG = P/L / Taxa de crescimento esperada do lucro", partes, f"{peg:.2f}")


def _calculo_ultimo_dividendo(contexto: ContextoCalculoIndicador | None, moeda: str) -> str | None:
    if not contexto or contexto.ultimo_dividendo_valor is None:
        return None
    data = contexto.ultimo_dividendo_data or "data nao informada"
    valor = formatar_moeda(contexto.ultimo_dividendo_valor, moeda)
    return _linha_calculo(
        "Ultimo dividendo = pagamento mais recente registrado na fonte",
        [
            ("Data do pagamento", data),
            ("Valor por acao", valor),
        ],
        f"{data} — {valor}",
    )


_MONTADORES = {
    "P/VPA": lambda info, moeda, ctx: _calculo_p_vpa(info, moeda, ctx),
    "VPA": lambda info, moeda, ctx: _calculo_vpa(info, moeda),
    "P/L (trailing)": lambda info, moeda, ctx: _calculo_p_l(
        info, moeda, ctx, "trailingPE", "trailingEps", "P/L trailing (fonte Yahoo)"
    ),
    "P/L (forward)": lambda info, moeda, ctx: _calculo_p_l(
        info, moeda, ctx, "forwardPE", "forwardEps", "P/L forward (fonte Yahoo)"
    ),
    "P/L": lambda info, moeda, ctx: _calculo_p_l(
        info, moeda, ctx, "priceEarnings", "earningsPerShare", "P/L (fonte Yahoo)"
    ),
    "P/Vendas": lambda info, moeda, ctx: _calculo_p_vendas(info, moeda, ctx),
    "PEG": lambda info, moeda, ctx: _calculo_peg(info),
    "Lucro por acao": lambda info, moeda, ctx: _calculo_lucro_por_acao(info, moeda),
    "Dividend yield": lambda info, moeda, ctx: _calculo_dividend_yield(info, moeda, ctx),
    "Margem bruta": lambda info, moeda, ctx: _calculo_margem(
        info, moeda, "grossMargins", "Margem bruta", "grossProfits"
    ),
    "Margem de lucro": lambda info, moeda, ctx: _calculo_margem(
        info, moeda, "profitMargins", "Margem de lucro", "netIncomeToCommon"
    ),
    "Margem operacional": lambda info, moeda, ctx: _calculo_margem(
        info, moeda, "operatingMargins", "Margem operacional", "operatingIncome"
    ),
    "ROE": lambda info, moeda, ctx: (
        _linha_calculo(
            "ROE = (Lucro liquido / Patrimonio liquido) x 100",
            [("ROE (fonte Yahoo)", formatar_percentual(_float_opcional(info.get("returnOnEquity"))))],
            formatar_percentual(_float_opcional(info.get("returnOnEquity"))),
        )
        if _float_opcional(info.get("returnOnEquity")) is not None
        else None
    ),
    "ROA": lambda info, moeda, ctx: (
        _linha_calculo(
            "ROA = (Lucro liquido / Ativos totais) x 100",
            [("ROA (fonte Yahoo)", formatar_percentual(_float_opcional(info.get("returnOnAssets"))))],
            formatar_percentual(_float_opcional(info.get("returnOnAssets"))),
        )
        if _float_opcional(info.get("returnOnAssets")) is not None
        else None
    ),
    "Capitalizacao": lambda info, moeda, ctx: _calculo_capitalizacao(info, moeda, ctx),
    "Variacao do dia": lambda info, moeda, ctx: _calculo_variacao_dia(info, moeda, ctx),
    "Variacao 52 semanas": lambda info, moeda, ctx: (
        _linha_calculo(
            "Variacao 52 semanas = variacao percentual do preco em 12 meses",
            [("Variacao informada pela fonte", formatar_percentual(_float_opcional(info.get("52WeekChange"))))],
            formatar_percentual(_float_opcional(info.get("52WeekChange"))),
        )
        if _float_opcional(info.get("52WeekChange")) is not None
        else None
    ),
    "Divida/Patrimonio": lambda info, moeda, ctx: (
        _linha_calculo(
            "Divida/Patrimonio = Divida total / Patrimonio liquido",
            [("Indice informado pela fonte", f"{_float_opcional(info.get('debtToEquity')):.2f}")],
            f"{_float_opcional(info.get('debtToEquity')):.2f}",
        )
        if _float_opcional(info.get("debtToEquity")) is not None
        else None
    ),
    "Liquidez corrente": lambda info, moeda, ctx: (
        _linha_calculo(
            "Liquidez corrente = Ativo circulante / Passivo circulante",
            [("Indice informado pela fonte", f"{_float_opcional(info.get('currentRatio')):.2f}")],
            f"{_float_opcional(info.get('currentRatio')):.2f}",
        )
        if _float_opcional(info.get("currentRatio")) is not None
        else None
    ),
    "Liquidez seca": lambda info, moeda, ctx: (
        _linha_calculo(
            "Liquidez seca = (Ativo circulante - Estoques) / Passivo circulante",
            [("Indice informado pela fonte", f"{_float_opcional(info.get('quickRatio')):.2f}")],
            f"{_float_opcional(info.get('quickRatio')):.2f}",
        )
        if _float_opcional(info.get("quickRatio")) is not None
        else None
    ),
    "Payout dividendos": lambda info, moeda, ctx: (
        _linha_calculo(
            "Payout = (Dividendos pagos / Lucro liquido) x 100",
            [("Payout informado pela fonte", formatar_percentual(_float_opcional(info.get("payoutRatio"))))],
            formatar_percentual(_float_opcional(info.get("payoutRatio"))),
        )
        if _float_opcional(info.get("payoutRatio")) is not None
        else None
    ),
    "Ultimo dividendo pago": lambda info, moeda, ctx: _calculo_ultimo_dividendo(ctx, moeda),
}


def montar_calculos_indicadores(
    info: dict,
    moeda: str,
    rotulos_presentes: set[str] | list[str],
    contexto: ContextoCalculoIndicador | None = None,
) -> dict[str, str]:
    """Retorna textos de calculo apenas para indicadores exibidos na tela."""
    calculos: dict[str, str] = {}
    for rotulo in rotulos_presentes:
        montador = _MONTADORES.get(rotulo)
        if montador is None:
            continue
        try:
            texto = montador(info, moeda, contexto)
        except (TypeError, ValueError, ZeroDivisionError):
            texto = None
        if texto and texto.strip():
            calculos[rotulo] = texto
    return calculos
