"""Formatacao de valores monetarios em pt-BR para a interface."""


def formatar_moeda(valor: float, moeda: str = "BRL") -> str:
    if moeda == "BRL":
        texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {texto}"
    return f"US$ {valor:,.2f}"


def formatar_variacao(valor: float, percentual: float, moeda: str = "BRL") -> str:
    sinal = "+" if percentual >= 0 else ""
    return f"{sinal}{percentual:.2f}% ({sinal}{formatar_moeda(valor, moeda)})"
