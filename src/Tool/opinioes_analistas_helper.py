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
from src.Tool.acao_b3_adr_helper import eh_acao_b3_para_adr, resolver_adr_eua_para_acao_b3
from src.Tool.bdrs_helper import eh_bdr_b3, resolver_ticker_eua_para_bdr
from src.Tool.cotacao_dual_helper import codigo_exibicao

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


def _pacote_tem_dados_uteis(pacote: OpinioesAnalistasPacote) -> bool:
    """Indica se ha recomendacao, precos-alvo ou historico utilizavel."""
    resumo = pacote.resumo
    if resumo.quantidade_analistas and resumo.quantidade_analistas > 0:
        return True
    if resumo.preco_alvo_medio is not None or resumo.preco_alvo_mediano is not None:
        return True
    if pacote.historico or pacote.movimentos:
        return True
    texto = (resumo.recomendacao_texto or "").strip()
    return bool(texto and texto not in {"—", "Sem cobertura"})


def _preencher_pacote_de_ticker(
    pacote: OpinioesAnalistasPacote,
    ticker: yf.Ticker,
) -> None:
    resumo = pacote.resumo

    try:
        info = ticker.info or {}
    except Exception:
        info = {}

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

    _preencher_movimentos_de_ticker(pacote, ticker)


def _preencher_movimentos_de_ticker(pacote: OpinioesAnalistasPacote, ticker: yf.Ticker) -> int:
    """Carrega upgrades/downgrades por instituicao. Retorna quantidade adicionada."""
    quantidade_antes = len(pacote.movimentos)
    try:
        df_mov = ticker.upgrades_downgrades
        if df_mov is None or df_mov.empty:
            return 0
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
        return 0
    return len(pacote.movimentos) - quantidade_antes


def _complementar_movimentos_via_adr(pacote: OpinioesAnalistasPacote, simbolo_b3: str) -> None:
    """Busca movimentos por instituicao no ADR nos EUA quando a B3 nao publica."""
    if pacote.movimentos:
        return
    if not eh_acao_b3_para_adr(simbolo_b3):
        return

    adr = resolver_adr_eua_para_acao_b3(simbolo_b3)
    if not adr:
        return

    adicionados = _preencher_movimentos_de_ticker(pacote, yf.Ticker(adr))
    if adicionados > 0:
        pacote.moeda_movimentos = "USD"
        pacote.avisos.insert(
            0,
            (
                f"Movimentos por instituicao obtidos via ADR nos EUA ({adr}). "
                "Precos-alvo dessa tabela em USD. O resumo acima permanece da acao na B3."
            ),
        )


def _aviso_movimentos_indisponiveis(pacote: OpinioesAnalistasPacote, simbolo: str) -> None:
    if pacote.movimentos:
        return
    if eh_bdr_b3(simbolo):
        pacote.avisos.append(
            "Movimentos individuais por instituicao nao disponiveis. "
            "Consolidacao via Yahoo Finance."
        )
        return
    if eh_acao_b3_para_adr(simbolo):
        pacote.avisos.append(
            "Movimentos por instituicao nao disponiveis para este ativo na B3. "
            "Tentamos complementar via ADR nos EUA, mas o Yahoo Finance nao retornou historico."
        )
        return
    pacote.avisos.append(
        "Movimentos individuais por instituicao nao disponiveis para este ativo. "
        "Exibimos a consolidacao de recomendacoes do Yahoo Finance."
    )


def _criar_pacote_base(simbolo: str, nome_empresa: str, moeda: str) -> OpinioesAnalistasPacote:
    codigo = codigo_exibicao(simbolo)
    return OpinioesAnalistasPacote(
        simbolo=simbolo,
        codigo=codigo,
        nome_empresa=nome_empresa or codigo,
        moeda=moeda or ("BRL" if simbolo.endswith(".SA") else "USD"),
    )


def _montar_de_simbolo(
    simbolo: str,
    nome_empresa: str,
    moeda: str,
    ticker: yf.Ticker | None = None,
) -> OpinioesAnalistasPacote:
    pacote = _criar_pacote_base(simbolo, nome_empresa, moeda)
    ticker_yf = ticker or yf.Ticker(simbolo)
    _preencher_pacote_de_ticker(pacote, ticker_yf)
    return pacote


def montar_opinioes_analistas(
    simbolo: str,
    nome_empresa: str,
    moeda: str,
    ticker: yf.Ticker | None = None,
) -> OpinioesAnalistasPacote | None:
    """Monta o pacote de opinioes; retorna None se nao houver dados uteis."""
    if simbolo.endswith("-USD"):
        return None

    pacote = _montar_de_simbolo(simbolo, nome_empresa, moeda, ticker=ticker)
    if _pacote_tem_dados_uteis(pacote):
        _complementar_movimentos_via_adr(pacote, simbolo)
        _aviso_movimentos_indisponiveis(pacote, simbolo)
        return pacote

    if eh_bdr_b3(simbolo):
        ticker_eua = resolver_ticker_eua_para_bdr(simbolo)
        if ticker_eua:
            pacote_eua = _montar_de_simbolo(ticker_eua, nome_empresa, "USD")
            if _pacote_tem_dados_uteis(pacote_eua):
                pacote_eua.codigo = codigo_exibicao(simbolo)
                pacote_eua.simbolo = simbolo
                if pacote_eua.movimentos:
                    pacote_eua.moeda_movimentos = "USD"
                pacote_eua.avisos.insert(
                    0,
                    (
                        f"O BDR {codigo_exibicao(simbolo)} nao possui cobertura de analistas na B3. "
                        f"Exibimos os dados do ativo subjacente nos EUA ({ticker_eua}). "
                        "Precos-alvo em USD."
                    ),
                )
                if not pacote_eua.movimentos:
                    _aviso_movimentos_indisponiveis(pacote_eua, simbolo)
                return pacote_eua

        pacote.avisos.insert(
            0,
            (
                "Este BDR nao possui cobertura de analistas na B3 no Yahoo Finance. "
                "Tambem nao encontramos dados do ativo subjacente nos EUA."
            ),
        )
        _complementar_movimentos_via_adr(pacote, simbolo)
        _aviso_movimentos_indisponiveis(pacote, simbolo)
        return pacote

    if pacote.resumo.recomendacao_texto == "Sem cobertura":
        pacote.avisos.insert(
            0,
            "O Yahoo Finance indica sem cobertura de analistas para este ativo.",
        )
        _complementar_movimentos_via_adr(pacote, simbolo)
        _aviso_movimentos_indisponiveis(pacote, simbolo)
        return pacote

    return None
