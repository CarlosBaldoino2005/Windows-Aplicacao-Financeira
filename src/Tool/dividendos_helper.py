"""Extracao e validacao de dividendos via Yahoo Finance."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import yfinance as yf

from src.Model.detalhes_acao import PagamentoDividendo
from src.Model.acoes_dividendos_universo import simbolo_esta_no_universo_dividendos
from src.Tool.registrador_log import RegistradorLog

_MAXIMO_PAGAMENTOS = 48


def eh_pagadora_dividendos(simbolo: str) -> bool:
    """Indica se a acao paga dividendos: lista curada ou historico/yield no Yahoo."""
    if simbolo.endswith("-USD"):
        return False
    if simbolo_esta_no_universo_dividendos(simbolo):
        return True

    try:
        ticker = yf.Ticker(simbolo)
        info = ticker.info or {}
        yield_val = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
        taxa = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
        if _float_positivo(yield_val) or _float_positivo(taxa):
            return True
        if _serie_dividendos_bruta(ticker) is not None:
            return True
    except Exception as exc:
        RegistradorLog().aviso(f"Verificacao de dividendos falhou para {simbolo}: {exc}")
    return False


def extrair_pagamentos_dividendos(
    simbolo: str, maximo: int = _MAXIMO_PAGAMENTOS
) -> list[PagamentoDividendo]:
    """Lista pagamentos (data e valor por cota), do mais recente ao mais antigo."""
    if simbolo.endswith("-USD"):
        return []

    try:
        ticker = yf.Ticker(simbolo)
        serie = _serie_dividendos_bruta(ticker)
    except Exception as exc:
        RegistradorLog().aviso(f"Dividendos Yahoo indisponiveis para {simbolo}: {exc}")
        return []

    if serie is None or serie.empty:
        return []

    pagamentos: list[PagamentoDividendo] = []
    for indice, valor in serie.sort_index(ascending=False).items():
        if valor != valor or float(valor) <= 0:
            continue
        data_obj = _normalizar_data(indice)
        pagamentos.append(
            PagamentoDividendo(
                data_pagamento=data_obj.strftime("%d/%m/%Y"),
                data_iso=data_obj.date().isoformat(),
                valor_por_cota=round(float(valor), 4),
            )
        )
        if len(pagamentos) >= maximo:
            break
    return pagamentos


def analisar_dividendos_periodo(
    simbolo: str,
    data_inicio_texto: str,
    data_fim_texto: str,
    moeda: str = "BRL",
) -> dict:
    """
    Cruza pagamentos com o intervalo do grafico.
    Se nao houve pagamento no periodo, retorna data/valor do ultimo dividendo anterior.
    """
    pagamentos = extrair_pagamentos_dividendos(simbolo)
    ultimo = pagamentos[0] if pagamentos else None

    dt_ini = _parse_data_interface(data_inicio_texto)
    dt_fim = _parse_data_interface(data_fim_texto)
    if dt_ini is None or dt_fim is None:
        return _montar_resumo_sem_periodo(ultimo, moeda, pagamentos)

    if dt_ini > dt_fim:
        dt_ini, dt_fim = dt_fim, dt_ini

    no_periodo: list[PagamentoDividendo] = []
    ultimo_antes: PagamentoDividendo | None = None

    for item in pagamentos:
        dt_pag = _parse_data_interface(item.data_pagamento)
        if dt_pag is None:
            continue
        if dt_ini <= dt_pag <= dt_fim:
            no_periodo.append(item)
        elif dt_pag < dt_ini:
            ultimo_antes = item
            break

    total_periodo = round(sum(p.valor_por_cota for p in no_periodo), 4)
    return {
        "dividendos_no_periodo": no_periodo,
        "total_dividendos_periodo": total_periodo,
        "houve_dividendo_no_periodo": len(no_periodo) > 0,
        "ultimo_dividendo_data": ultimo_antes.data_pagamento if ultimo_antes else "",
        "ultimo_dividendo_valor": ultimo_antes.valor_por_cota if ultimo_antes else None,
        "ultimo_dividendo_global_data": ultimo.data_pagamento if ultimo else "",
        "ultimo_dividendo_global_valor": ultimo.valor_por_cota if ultimo else None,
        "moeda_dividendo": moeda,
        "texto_resumo": _texto_resumo_dividendos(
            no_periodo, ultimo_antes, ultimo, moeda, data_inicio_texto, data_fim_texto
        ),
    }


def _serie_dividendos_bruta(ticker: yf.Ticker) -> pd.Series | None:
    """Obtem serie de dividendos (ticker.dividends ou coluna Dividends em actions)."""
    try:
        serie = ticker.dividends
        if serie is not None and not serie.empty:
            return serie.dropna()
    except Exception:
        pass

    try:
        acoes = ticker.actions
        if acoes is not None and not acoes.empty and "Dividends" in acoes.columns:
            coluna = acoes["Dividends"].dropna()
            coluna = coluna[coluna > 0]
            if not coluna.empty:
                return coluna
    except Exception:
        pass

    return None


def _texto_resumo_dividendos(
    no_periodo: list[PagamentoDividendo],
    ultimo_antes: PagamentoDividendo | None,
    ultimo_global: PagamentoDividendo | None,
    moeda: str,
    data_inicio: str,
    data_fim: str,
) -> str:
    from src.View.formatadores import formatar_moeda

    if no_periodo:
        linhas = [
            f"Dividendos pagos entre {data_inicio} e {data_fim}:",
        ]
        for item in no_periodo:
            linhas.append(
                f"  • {item.data_pagamento} — {formatar_moeda(item.valor_por_cota, moeda)} por acao"
            )
        total = sum(p.valor_por_cota for p in no_periodo)
        linhas.append(f"Total no periodo: {formatar_moeda(total, moeda)} por acao")
        return "\n".join(linhas)

    if ultimo_antes:
        return (
            f"Nenhum dividendo pago entre {data_inicio} e {data_fim}.\n"
            f"Ultimo dividendo pago antes do periodo: {ultimo_antes.data_pagamento} — "
            f"{formatar_moeda(ultimo_antes.valor_por_cota, moeda)} por acao."
        )

    if ultimo_global:
        return (
            f"Nenhum dividendo pago entre {data_inicio} e {data_fim}.\n"
            f"Ultimo dividendo registrado: {ultimo_global.data_pagamento} — "
            f"{formatar_moeda(ultimo_global.valor_por_cota, moeda)} por acao."
        )

    return "Historico de dividendos nao disponivel para esta empresa no Yahoo Finance."


def _montar_resumo_sem_periodo(
    ultimo: PagamentoDividendo | None,
    moeda: str,
    pagamentos: list[PagamentoDividendo],
) -> dict:
    from src.View.formatadores import formatar_moeda

    texto = "Historico de dividendos nao disponivel para esta empresa no Yahoo Finance."
    if ultimo:
        texto = (
            f"Ultimo dividendo registrado: {ultimo.data_pagamento} — "
            f"{formatar_moeda(ultimo.valor_por_cota, moeda)} por acao."
        )
    return {
        "dividendos_no_periodo": [],
        "total_dividendos_periodo": 0.0,
        "houve_dividendo_no_periodo": False,
        "ultimo_dividendo_data": ultimo.data_pagamento if ultimo else "",
        "ultimo_dividendo_valor": ultimo.valor_por_cota if ultimo else None,
        "ultimo_dividendo_global_data": ultimo.data_pagamento if ultimo else "",
        "ultimo_dividendo_global_valor": ultimo.valor_por_cota if ultimo else None,
        "moeda_dividendo": moeda,
        "texto_resumo": texto,
        "pagamentos_disponiveis": len(pagamentos),
    }


def _parse_data_interface(texto: str) -> datetime | None:
    if not texto or not str(texto).strip():
        return None
    limpo = str(texto).strip().split(" ")[0]
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(limpo, formato)
        except ValueError:
            continue
    return None


def _normalizar_data(indice) -> datetime:
    data_obj = indice.to_pydatetime() if hasattr(indice, "to_pydatetime") else indice
    if hasattr(data_obj, "tzinfo") and data_obj.tzinfo is not None:
        data_obj = data_obj.replace(tzinfo=None)
    return data_obj


def _float_positivo(valor) -> bool:
    if valor is None:
        return False
    try:
        return float(valor) > 0
    except (TypeError, ValueError):
        return False
