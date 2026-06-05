"""Universo de FIIs (fundos imobiliarios) da B3 para o painel dedicado."""

LIMITE_FIIS_PAINEL = 15
QUANTIDADE_PADRAO_FIIS = 15
QUANTIDADE_MAXIMA_FIIS = 80

# Tickers 11 que sao units/acoes, nao fundos imobiliarios.
UNIDADES_NAO_FII = frozenset(
    {
        "TAEE11",
        "SANB11",
        "SAPR11",
        "KLBN11",
        "BPAC11",
    }
)

FIIS_B3 = [
    "HGLG11",
    "XPLG11",
    "MXRF11",
    "KNCR11",
    "KNRI11",
    "HGRU11",
    "BCFF11",
    "RBRR11",
    "VISC11",
    "LVBI11",
    "HFOF11",
    "XPML11",
    "BTLG11",
    "RECR11",
    "VILG11",
    "PVBI11",
    "GARE11",
    "IRIM11",
    "CPTS11",
    "HSML11",
    "JSRE11",
    "GGRC11",
    "VRTA11",
    "MCCI11",
    "RZAK11",
    "TGAR11",
    "TRXF11",
    "KNSC11",
    "BRCO11",
    "XPCI11",
    "HABT11",
    "VCJR11",
    "MGFF11",
    "RBVA11",
    "MALL11",
    "DEVA11",
    "JSAF11",
    "ALZR11",
    "BRCR11",
    "HSLG11",
    "KNHF11",
    "VGHF11",
    "HGRE11",
    "RBRF11",
    "PLCR11",
    "SNCI11",
    "BTCI11",
    "MFII11",
    "QAGR11",
    "CVBI11",
    "RZTR11",
]


def montar_lista_fiis_monitorados(limite: int = LIMITE_FIIS_PAINEL) -> list[str]:
    """Monta tickers Yahoo (.SA) ate o limite informado."""
    resultado: list[str] = []
    vistos: set[str] = set()

    for codigo in FIIS_B3:
        simbolo = f"{codigo}.SA" if not codigo.endswith(".SA") else codigo
        if simbolo not in vistos:
            vistos.add(simbolo)
            resultado.append(simbolo)
        if len(resultado) >= limite:
            return resultado[:limite]

    return resultado[:limite]


def simbolo_esta_no_universo_fiis(simbolo: str) -> bool:
    """Verifica se o ticker faz parte da lista curada de FIIs."""
    limpo = simbolo.strip().upper()
    codigo = limpo.replace(".SA", "")
    return codigo in FIIS_B3
