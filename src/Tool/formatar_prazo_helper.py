"""Formata prazos longos com dias no titulo e decomposicao em anos, meses e dias."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from src.Tool.mascara_moeda_helper import formatar_inteiro_ptbr
from src.Tool.validadores import validar_data_ptbr

_DIAS_POR_MES = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


@dataclass(frozen=True)
class PrazoLegivel:
    """Textos prontos para exibir vencimento ou periodo de simulacao."""

    dias_totais: int
    titulo: str
    descricao: str
    intervalo: str = ""


def formatar_contagem_dias(dias: int) -> str:
    """Ex.: 2547 -> '2.547 dias'."""
    quantidade = max(0, int(dias))
    texto = formatar_inteiro_ptbr(quantidade)
    return f"{texto} dia" if quantidade == 1 else f"{texto} dias"


def formatar_decomposicao_prazo(anos: int, meses: int, dias: int) -> str:
    """Monta 'X anos + Y meses + Z dias' omitindo partes zeradas quando possivel."""
    partes: list[str] = []
    if anos > 0:
        partes.append(f"{anos} ano" if anos == 1 else f"{anos} anos")
    if meses > 0:
        partes.append(f"{meses} mes" if meses == 1 else f"{meses} meses")
    if dias > 0 or not partes:
        partes.append(f"{dias} dia" if dias == 1 else f"{dias} dias")
    return " + ".join(partes)


def _parse_data(valor: date | datetime | str | None) -> date | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    if not texto:
        return None
    if len(texto) >= 10 and texto[4] == "-":
        try:
            return datetime.strptime(texto[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    dt, erro = validar_data_ptbr(texto[:10] if len(texto) > 10 else texto)
    if erro or dt is None:
        return None
    return dt.date()


def _bissexto(ano: int) -> bool:
    return ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)


def _dias_no_mes(ano: int, mes: int) -> int:
    if mes == 2 and _bissexto(ano):
        return 29
    return _DIAS_POR_MES[mes - 1]


def _adicionar_meses(data_ref: date, meses: int) -> date:
    """Soma meses mantendo o dia quando existir no mes destino."""
    total_meses = data_ref.month - 1 + meses
    ano = data_ref.year + total_meses // 12
    mes = total_meses % 12 + 1
    dia = min(data_ref.day, _dias_no_mes(ano, mes))
    return date(ano, mes, dia)


def decompor_periodo_em_anos_meses_dias(inicio: date, fim: date) -> tuple[int, int, int]:
    """Decomposicao calendario entre duas datas (fim >= inicio)."""
    if fim < inicio:
        return 0, 0, 0

    anos = 0
    cursor = inicio
    while True:
        proximo = date(cursor.year + 1, cursor.month, min(cursor.day, _dias_no_mes(cursor.year + 1, cursor.month)))
        if proximo > fim:
            break
        anos += 1
        cursor = proximo

    meses = 0
    while True:
        proximo = _adicionar_meses(cursor, 1)
        if proximo > fim:
            break
        meses += 1
        cursor = proximo

    dias = (fim - cursor).days
    return anos, meses, dias


def montar_prazo_legivel(
    dias: int | None = None,
    data_fim: date | datetime | str | None = None,
    data_inicio: date | datetime | str | None = None,
    incluir_data_no_titulo: bool = True,
) -> PrazoLegivel:
    """
    Monta titulo com contagem de dias e descricao decomposta.
    Prioriza datas informadas; se so houver dias, projeta a partir de hoje.
    """
    inicio = _parse_data(data_inicio) or date.today()
    fim = _parse_data(data_fim)

    if fim is None and dias is not None:
        fim = inicio + timedelta(days=max(0, int(dias)))
    elif fim is not None and dias is None:
        dias = max(0, (fim - inicio).days)
    elif fim is not None and dias is not None:
        dias = max(0, int(dias))
    else:
        dias = 0
        fim = inicio

    if fim < inicio:
        fim = inicio
        dias = 0

    anos, meses, dias_restantes = decompor_periodo_em_anos_meses_dias(inicio, fim)
    contagem = formatar_contagem_dias(dias)
    fim_texto = fim.strftime("%d/%m/%Y")
    inicio_texto = inicio.strftime("%d/%m/%Y")

    if incluir_data_no_titulo and fim != inicio:
        titulo = f"{fim_texto} ({contagem})"
    else:
        titulo = contagem

    intervalo = ""
    if inicio != fim:
        intervalo = f"De {inicio_texto} ate {fim_texto}"

    return PrazoLegivel(
        dias_totais=dias,
        titulo=titulo,
        descricao=formatar_decomposicao_prazo(anos, meses, dias_restantes),
        intervalo=intervalo,
    )


def montar_texto_celula_prazo(prazo: PrazoLegivel) -> str:
    """Duas linhas para grids: titulo com dias e decomposicao abaixo."""
    return f"{prazo.titulo}\n{prazo.descricao}"


def montar_texto_bloco_periodo(prazo: PrazoLegivel, complemento: str = "") -> str:
    """Corpo de card de periodo com decomposicao, intervalo e texto extra."""
    linhas = [prazo.descricao]
    if prazo.intervalo:
        linhas.append(prazo.intervalo)
    if complemento:
        linhas.append(complemento)
    return "\n".join(linhas)
