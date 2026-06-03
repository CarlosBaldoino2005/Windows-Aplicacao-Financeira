"""Periodos padrao para graficos e paineis de mercado."""

PERIODOS_MERCADO: list[tuple[str, str]] = [
    ("dia", "Dia"),
    ("semana", "Semana"),
    ("mes", "Mes"),
    ("trimestre", "Trimestre"),
    ("semestre", "Semestre"),
    ("ano", "Ano"),
    ("personalizado", "Personalizado"),
]


def periodo_chave_por_rotulo(rotulo: str) -> str:
    for chave, nome in PERIODOS_MERCADO:
        if nome == rotulo:
            return chave
    return "mes"


def rotulo_periodo_por_chave(chave: str) -> str:
    for chave_item, nome in PERIODOS_MERCADO:
        if chave_item == chave:
            return nome
    return chave
