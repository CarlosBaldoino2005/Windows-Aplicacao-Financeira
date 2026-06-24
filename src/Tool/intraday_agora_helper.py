"""Completa serie intraday com cotacao ao vivo quando os candles atrasam."""
from __future__ import annotations

from datetime import date, datetime, time

from src.Model.cotacao import PontoHistorico
from src.Service.provedores.util_provedor import data_para_exibicao
from src.View.grafico_helper import extrair_minutos_dia_de_ponto


def calcular_atraso_candles_minutos(
    pontos: list[PontoHistorico],
    *,
    agora: datetime | None = None,
) -> int | None:
    """Minutos entre o ultimo candle real e o horario atual."""
    if not pontos:
        return None

    referencia = _normalizar_minuto(agora or datetime.now())
    minutos_ultimo = extrair_minutos_dia_de_ponto(
        pontos[-1].data_exibicao,
        data_iso=pontos[-1].data_iso,
    )
    if minutos_ultimo is None:
        return None

    minutos_agora = referencia.hour * 60 + referencia.minute
    atraso = minutos_agora - int(minutos_ultimo)
    return atraso if atraso > 0 else None


def completar_serie_intraday_com_cotacao(
    pontos: list[PontoHistorico],
    preco_atual: float | None,
    *,
    agora: datetime | None = None,
) -> list[PontoHistorico]:
    """
    Preenche o vao entre o ultimo candle do provedor e o minuto atual.

    Os candles do Yahoo para B3 costumam atrasar ~15 min; a cotacao ao vivo
    e usada para estender o grafico ate o horario presente.
    """
    if not pontos or preco_atual is None or preco_atual <= 0:
        return pontos

    referencia = _normalizar_minuto(agora or datetime.now())
    ultimo = pontos[-1]
    minutos_ultimo = extrair_minutos_dia_de_ponto(ultimo.data_exibicao, data_iso=ultimo.data_iso)
    if minutos_ultimo is None:
        return pontos

    minutos_agora = referencia.hour * 60 + referencia.minute
    if minutos_agora < minutos_ultimo:
        return pontos

    preco_vivo = round(float(preco_atual), 2)
    data_ref = _data_do_ponto(ultimo, referencia.date())

    if int(minutos_agora) == int(minutos_ultimo):
        return [
            *pontos[:-1],
            PontoHistorico(
                data_iso=ultimo.data_iso,
                data_exibicao=ultimo.data_exibicao,
                preco_fechamento=preco_vivo,
                preco_abertura=ultimo.preco_abertura,
                preco_maxima=_extremo_maximo(ultimo.preco_maxima, ultimo.preco_fechamento, preco_vivo),
                preco_minima=_extremo_minimo(ultimo.preco_minima, ultimo.preco_fechamento, preco_vivo),
                volume=ultimo.volume,
            ),
        ]

    resultado = list(pontos)
    preco_intermediario = ultimo.preco_fechamento

    for minuto in range(int(minutos_ultimo) + 1, int(minutos_agora)):
        resultado.append(
            _criar_ponto_sintetico(
                minuto,
                preco_intermediario,
                data_ref,
            )
        )

    resultado.append(
        _criar_ponto_sintetico(
            int(minutos_agora),
            preco_vivo,
            data_ref,
        )
    )
    return resultado


def _normalizar_minuto(valor: datetime) -> datetime:
    return valor.replace(second=0, microsecond=0)


def _data_do_ponto(ponto: PontoHistorico, data_padrao: date) -> date:
    texto = (ponto.data_exibicao or "").strip()
    if len(texto) >= 10 and texto[2] == "/" and texto[5] == "/":
        try:
            dia, mes, ano = map(int, texto[:10].split("/"))
            return date(ano, mes, dia)
        except ValueError:
            pass

    if ponto.data_iso:
        try:
            return datetime.fromisoformat(ponto.data_iso.replace("Z", "+00:00")).date()
        except ValueError:
            pass

    return data_padrao


def _extremo_maximo(*valores: float | None) -> float | None:
    numeros = [float(valor) for valor in valores if valor is not None]
    return max(numeros) if numeros else None


def _extremo_minimo(*valores: float | None) -> float | None:
    numeros = [float(valor) for valor in valores if valor is not None]
    return min(numeros) if numeros else None


def _criar_ponto_sintetico(minutos_dia: int, preco: float, data_ref: date) -> PontoHistorico:
    hora = minutos_dia // 60
    minuto = minutos_dia % 60
    data_obj = datetime.combine(data_ref, time(hora, minuto))
    return PontoHistorico(
        data_iso=data_obj.isoformat(),
        data_exibicao=data_para_exibicao(data_obj),
        preco_fechamento=preco,
        preco_abertura=preco,
        preco_maxima=preco,
        preco_minima=preco,
        volume=None,
    )
