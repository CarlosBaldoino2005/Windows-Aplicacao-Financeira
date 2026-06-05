"""Busca e normaliza opinioes de analistas via Yahoo Finance."""
from __future__ import annotations

from datetime import datetime

import yfinance as yf

from src.Model.opinioes_analistas import (
    HistoricoRecomendacaoPeriodo,
    MovimentoAnalista,
    OpinioesAnalistasPacote,
    ResumoOpinioesAnalistas,
)

_TRADUCAO_NOTA = {
    "buy": "Comprar",
    "hold": "Manter",
    "sell": "Vender",
    "strong_buy": "Compra forte",
    "strongbuy": "Compra forte",
    "strong_sell": "Venda forte",
    "strongsell": "Venda forte",
    "outperform": "Superar mercado",
    "underperform": "Abaixo do mercado",
    "neutral": "Neutro",
    "overweight": "Peso acima",
    "underweight": "Peso abaixo",
    "equal_weight": "Peso igual",
    "equal-weight": "Peso igual",
    "market perform": "Desempenho de mercado",
    "sector perform": "Desempenho do setor",
    "positive": "Positivo",
    "negative": "Negativo",
    "none": "Sem cobertura",
}


def traduzir_nota_analista(valor: str | None) -> str:
    """Converte notas em ingles para rotulos em pt-BR."""
    if not valor or not str(valor).strip():
        return "—"
    texto = str(valor).strip()
    chave = texto.lower().replace(" ", "_").replace("-", "_")
    return _TRADUCAO_NOTA.get(chave, texto)


def _traduzir_periodo(periodo: str) -> str:
    texto = str(periodo or "").strip().lower()
    if texto == "0m":
        return "Mes atual"
    if texto.endswith("m") and texto.startswith("-"):
        try:
            meses = int(texto[1:-1])
            return f"{meses} mes{'es' if meses > 1 else ''} atras"
        except ValueError:
            pass
    return str(periodo)


def _float_opcional(valor) -> float | None:
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _int_opcional(valor) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return None


def _formatar_data(valor) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    texto = str(valor).strip()
    if not texto:
        return "—"
    try:
        if "T" in texto:
            texto = texto.replace("Z", "+00:00")
        if "+" in texto[10:]:
            parte = texto.split("+", 1)[0]
        else:
            parte = texto.split("-", 3)
            parte = "-".join(parte[:3]) if len(parte) >= 3 else texto
        dt = datetime.fromisoformat(parte.replace(" ", "T")[:19])
        return dt.strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return texto[:10] if len(texto) >= 10 else texto


def montar_opinioes_analistas(
    simbolo: str,
    nome_empresa: str,
    moeda: str,
    ticker: yf.Ticker | None = None,
) -> OpinioesAnalistasPacote | None:
    """Monta o pacote de opinioes; retorna None se nao houver dados uteis."""
    if simbolo.endswith("-USD"):
        return None

    codigo = simbolo.replace(".SA", "")
    pacote = OpinioesAnalistasPacote(
        simbolo=simbolo,
        codigo=codigo,
        nome_empresa=nome_empresa or codigo,
        moeda=moeda or ("BRL" if simbolo.endswith(".SA") else "USD"),
    )

    try:
        ticker = ticker or yf.Ticker(simbolo)
        info = ticker.info or {}
    except Exception:
        info = {}

    resumo = pacote.resumo
    resumo.recomendacao_texto = traduzir_nota_analista(str(info.get("recommendationKey") or ""))
    resumo.recomendacao_media = _float_opcional(info.get("recommendationMean"))
    resumo.nota_media_descricao = str(info.get("averageAnalystRating") or "").strip()
    resumo.quantidade_analistas = _int_opcional(info.get("numberOfAnalystOpinions"))
    resumo.preco_alvo_min = _float_opcional(info.get("targetLowPrice"))
    resumo.preco_alvo_medio = _float_opcional(info.get("targetMeanPrice"))
    resumo.preco_alvo_max = _float_opcional(info.get("targetHighPrice"))
    resumo.preco_alvo_mediano = _float_opcional(info.get("targetMedianPrice"))

    try:
        df_hist = ticker.recommendations
        if df_hist is not None and not df_hist.empty:
            for _, linha in df_hist.iterrows():
                pacote.historico.append(
                    HistoricoRecomendacaoPeriodo(
                        periodo=_traduzir_periodo(str(linha.get("period", ""))),
                        compra_forte=int(linha.get("strongBuy") or 0),
                        comprar=int(linha.get("buy") or 0),
                        manter=int(linha.get("hold") or 0),
                        vender=int(linha.get("sell") or 0),
                        venda_forte=int(linha.get("strongSell") or 0),
                    )
                )
            atual = pacote.historico[0]
            resumo.compra_forte = atual.compra_forte
            resumo.comprar = atual.comprar
            resumo.manter = atual.manter
            resumo.vender = atual.vender
            resumo.venda_forte = atual.venda_forte
    except Exception:
        pacote.avisos.append("Historico mensal de recomendacoes indisponivel.")

    try:
        df_mov = ticker.upgrades_downgrades
        if df_mov is not None and not df_mov.empty:
            for indice, linha in df_mov.head(40).iterrows():
                pacote.movimentos.append(
                    MovimentoAnalista(
                        data=_formatar_data(indice),
                        instituicao=str(linha.get("Firm") or "—"),
                        nota_anterior=traduzir_nota_analista(str(linha.get("FromGrade") or "")),
                        nota_nova=traduzir_nota_analista(str(linha.get("ToGrade") or "")),
                        acao=str(linha.get("Action") or "—"),
                        preco_alvo=_float_opcional(linha.get("currentPriceTarget")),
                        preco_alvo_anterior=_float_opcional(linha.get("priorPriceTarget")),
                    )
                )
    except Exception:
        pass

    tem_resumo = any(
        [
            resumo.recomendacao_texto and resumo.recomendacao_texto != "—",
            resumo.quantidade_analistas,
            resumo.preco_alvo_medio is not None,
            pacote.historico,
            pacote.movimentos,
        ]
    )
    if not tem_resumo:
        return None

    if not pacote.movimentos:
        pacote.avisos.append(
            "Movimentos individuais por instituicao nao disponiveis para este ativo. "
            "Exibimos a consolidacao de recomendacoes do Yahoo Finance."
        )
    return pacote
