"""Semana do calendario visual: domingo a sabado."""
from __future__ import annotations

import calendar

ROTULOS_DIAS_SEMANA_DOMINGO = ("Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab")

_calendario_domingo = calendar.Calendar(firstweekday=calendar.SUNDAY)


def obter_semanas_mes_calendario(ano: int, mes: int) -> list[list[int]]:
    """Matriz do mes com semanas iniciando no domingo (0 = celula vazia)."""
    return _calendario_domingo.monthdayscalendar(ano, mes)
