"""Formatacao de valores monetarios em pt-BR para a interface."""


def formatar_moeda(valor: float, moeda: str = "BRL") -> str:
    if moeda == "BRL":
        texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {texto}"
    return f"US$ {valor:,.2f}"


def formatar_variacao(valor: float, percentual: float, moeda: str = "BRL") -> str:
    sinal = "+" if percentual >= 0 else ""
    return f"{sinal}{percentual:.2f}% ({sinal}{formatar_moeda(valor, moeda)})"


def formatar_variacao_com_rotulo(
    valor: float,
    percentual: float,
    rotulo: str,
    moeda: str = "BRL",
) -> str:
    """Variacao com icone de tendencia e rotulo (ex.: Hoje, Na sua compra)."""
    icone = "▲" if percentual >= 0 else "▼"
    return f"{icone} {formatar_variacao(valor, percentual, moeda)} {rotulo}"


def formatar_percentual(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor * 100:.{casas}f}%"


def formatar_numero_grande(valor: float | None, moeda: str = "BRL") -> str:
    """Formata valores muito grandes (bilhoes/milhoes) para leitura em pt-BR."""
    if valor is None:
        return "—"

    absoluto = abs(valor)
    sinal = "-" if valor < 0 else ""

    if absoluto >= 1_000_000_000_000:
        texto = f"{absoluto / 1_000_000_000_000:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        sufixo = " tri"
    elif absoluto >= 1_000_000_000:
        texto = f"{absoluto / 1_000_000_000:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        sufixo = " bi"
    elif absoluto >= 1_000_000:
        texto = f"{absoluto / 1_000_000:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        sufixo = " mi"
    else:
        return f"{sinal}{formatar_moeda(valor, moeda).replace('R$ ', '').replace('US$ ', '')}"

    prefixo = "R$ " if moeda == "BRL" else "US$ "
    return f"{sinal}{prefixo}{texto}{sufixo}"


def formatar_texto_opcional(valor: str | int | float | None) -> str:
    if valor is None or valor == "":
        return "—"
    return str(valor)
