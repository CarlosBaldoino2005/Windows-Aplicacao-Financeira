"""Catalogo de servidores/fontes de noticias (agregados via Yahoo Finance)."""
from __future__ import annotations

from dataclasses import dataclass

CATEGORIA_MERCADO = "mercado"
CATEGORIA_CRIPTO = "cripto"

PROVEDOR_PADRAO_MERCADO = "geral"
PROVEDOR_PADRAO_CRIPTO = "cripto_geral"


@dataclass(frozen=True)
class ProvedorNoticias:
    """Um provedor de manchetes com tickers de referencia no Yahoo Finance."""

    chave: str
    nome: str
    descricao: str
    categoria: str
    regiao_foco: str
    fontes: tuple[tuple[str, str], ...]


def _provedores_mercado() -> list[ProvedorNoticias]:
    return [
        ProvedorNoticias(
            chave="geral",
            nome="Geral (Brasil + EUA)",
            descricao="Ibovespa, ETF Brasil e indices EUA.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="Global",
            fontes=(
                ("^BVSP", "Brasil"),
                ("EWZ", "Brasil"),
                ("SPY", "EUA"),
                ("^GSPC", "EUA"),
            ),
        ),
        ProvedorNoticias(
            chave="brasil_ibovespa",
            nome="Brasil — Ibovespa",
            descricao="Indice Bovespa e ETF iShares Brasil.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="Brasil",
            fontes=(
                ("^BVSP", "Brasil"),
                ("EWZ", "Brasil"),
                ("BOVA11.SA", "Brasil"),
            ),
        ),
        ProvedorNoticias(
            chave="brasil_blue_chips",
            nome="Brasil — Blue chips",
            descricao="Petrobras, Vale, Itau, Bradesco e Weg.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="Brasil",
            fontes=(
                ("PETR4.SA", "Brasil"),
                ("VALE3.SA", "Brasil"),
                ("ITUB4.SA", "Brasil"),
                ("BBDC4.SA", "Brasil"),
                ("WEGE3.SA", "Brasil"),
                ("ABEV3.SA", "Brasil"),
            ),
        ),
        ProvedorNoticias(
            chave="brasil_bancos",
            nome="Brasil — Bancos e financeiras",
            descricao="Grandes bancos e seguradoras listadas na B3.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="Brasil",
            fontes=(
                ("ITUB4.SA", "Brasil"),
                ("BBDC4.SA", "Brasil"),
                ("BBAS3.SA", "Brasil"),
                ("SANB11.SA", "Brasil"),
                ("BBSE3.SA", "Brasil"),
                ("BPAC11.SA", "Brasil"),
            ),
        ),
        ProvedorNoticias(
            chave="eua_wall_street",
            nome="EUA — Wall Street",
            descricao="S&P 500, Nasdaq e Dow Jones.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="EUA",
            fontes=(
                ("^GSPC", "EUA"),
                ("SPY", "EUA"),
                ("^IXIC", "EUA"),
                ("QQQ", "EUA"),
                ("DIA", "EUA"),
            ),
        ),
        ProvedorNoticias(
            chave="eua_tecnologia",
            nome="EUA — Tecnologia",
            descricao="Big tech e ETF Nasdaq.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="EUA",
            fontes=(
                ("AAPL", "EUA"),
                ("MSFT", "EUA"),
                ("GOOGL", "EUA"),
                ("NVDA", "EUA"),
                ("META", "EUA"),
                ("QQQ", "EUA"),
            ),
        ),
        ProvedorNoticias(
            chave="eua_financeiro",
            nome="EUA — Financeiro",
            descricao="Bancos, pagamentos e seguros americanos.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="EUA",
            fontes=(
                ("JPM", "EUA"),
                ("BAC", "EUA"),
                ("GS", "EUA"),
                ("V", "EUA"),
                ("MA", "EUA"),
                ("BRK-B", "EUA"),
            ),
        ),
        ProvedorNoticias(
            chave="europa",
            nome="Europa",
            descricao="ETFs e referencias da Europa.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="Europa",
            fontes=(
                ("FEZ", "Europa"),
                ("EZU", "Europa"),
                ("EWG", "Europa"),
                ("^STOXX50E", "Europa"),
                ("VGK", "Europa"),
            ),
        ),
        ProvedorNoticias(
            chave="asia",
            nome="Asia",
            descricao="China, Japao e India via ETFs.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="Asia",
            fontes=(
                ("FXI", "Asia"),
                ("EWJ", "Asia"),
                ("INDA", "Asia"),
                ("MCHI", "Asia"),
                ("^N225", "Asia"),
            ),
        ),
        ProvedorNoticias(
            chave="mundo_emergentes",
            nome="Mundo — Emergentes",
            descricao="Mercados emergentes e commodities basicas.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="Global",
            fontes=(
                ("EEM", "Global"),
                ("EWZ", "Brasil"),
                ("INDA", "Asia"),
                ("FXI", "Asia"),
                ("RSX", "Global"),
            ),
        ),
        ProvedorNoticias(
            chave="commodities",
            nome="Commodities",
            descricao="Petróleo, ouro, prata e energia.",
            categoria=CATEGORIA_MERCADO,
            regiao_foco="Global",
            fontes=(
                ("CL=F", "Global"),
                ("BZ=F", "Brasil"),
                ("GC=F", "Global"),
                ("SI=F", "Global"),
                ("NG=F", "Global"),
            ),
        ),
    ]


def _provedores_cripto() -> list[ProvedorNoticias]:
    return [
        ProvedorNoticias(
            chave="cripto_geral",
            nome="Cripto — Principais",
            descricao="Bitcoin, Ethereum e altcoins de referencia.",
            categoria=CATEGORIA_CRIPTO,
            regiao_foco="Cripto",
            fontes=(
                ("BTC-USD", "Cripto"),
                ("ETH-USD", "Cripto"),
                ("SOL-USD", "Cripto"),
                ("BNB-USD", "Cripto"),
                ("XRP-USD", "Cripto"),
                ("DOGE-USD", "Cripto"),
            ),
        ),
        ProvedorNoticias(
            chave="cripto_top3",
            nome="Cripto — Top 3",
            descricao="Bitcoin, Ethereum e Solana.",
            categoria=CATEGORIA_CRIPTO,
            regiao_foco="Cripto",
            fontes=(
                ("BTC-USD", "Cripto"),
                ("ETH-USD", "Cripto"),
                ("SOL-USD", "Cripto"),
            ),
        ),
        ProvedorNoticias(
            chave="cripto_altcoins",
            nome="Cripto — Altcoins",
            descricao="Solana, BNB, XRP, Dogecoin e Cardano.",
            categoria=CATEGORIA_CRIPTO,
            regiao_foco="Cripto",
            fontes=(
                ("SOL-USD", "Cripto"),
                ("BNB-USD", "Cripto"),
                ("XRP-USD", "Cripto"),
                ("DOGE-USD", "Cripto"),
                ("ADA-USD", "Cripto"),
                ("AVAX-USD", "Cripto"),
            ),
        ),
        ProvedorNoticias(
            chave="cripto_bitcoin",
            nome="Cripto — Bitcoin",
            descricao="Somente manchetes ligadas ao Bitcoin.",
            categoria=CATEGORIA_CRIPTO,
            regiao_foco="Cripto",
            fontes=(("BTC-USD", "Cripto"),),
        ),
        ProvedorNoticias(
            chave="cripto_ethereum",
            nome="Cripto — Ethereum",
            descricao="Somente manchetes ligadas ao Ethereum.",
            categoria=CATEGORIA_CRIPTO,
            regiao_foco="Cripto",
            fontes=(("ETH-USD", "Cripto"),),
        ),
    ]


_PROVEDORES: dict[str, ProvedorNoticias] = {}
for item in _provedores_mercado() + _provedores_cripto():
    _PROVEDORES[item.chave] = item


def listar_provedores(categoria: str = CATEGORIA_MERCADO) -> list[ProvedorNoticias]:
    return [p for p in _PROVEDORES.values() if p.categoria == categoria]


def obter_provedor(chave: str, categoria: str = CATEGORIA_MERCADO) -> ProvedorNoticias | None:
    item = _PROVEDORES.get((chave or "").strip().lower())
    if item is None or item.categoria != categoria:
        return None
    return item


def resolver_provedor(
    chave: str | None,
    categoria: str = CATEGORIA_MERCADO,
) -> ProvedorNoticias:
    padrao = PROVEDOR_PADRAO_CRIPTO if categoria == CATEGORIA_CRIPTO else PROVEDOR_PADRAO_MERCADO
    item = obter_provedor(chave or "", categoria)
    if item is not None:
        return item
    item_padrao = _PROVEDORES.get(padrao)
    if item_padrao is not None:
        return item_padrao
    lista = listar_provedores(categoria)
    return lista[0]


def rotulo_por_chave(chave: str, categoria: str = CATEGORIA_MERCADO) -> str:
    item = obter_provedor(chave, categoria)
    return item.nome if item else resolver_provedor(None, categoria).nome


def chave_por_rotulo(rotulo: str, categoria: str = CATEGORIA_MERCADO) -> str:
    texto = (rotulo or "").strip()
    for item in listar_provedores(categoria):
        if item.nome == texto:
            return item.chave
    return (
        PROVEDOR_PADRAO_CRIPTO
        if categoria == CATEGORIA_CRIPTO
        else PROVEDOR_PADRAO_MERCADO
    )


def simbolo_permitido_no_provedor(simbolo: str, provedor: ProvedorNoticias) -> bool:
    """Restringe buscas por ticker ao foco regional do provedor escolhido."""
    if provedor.chave in (PROVEDOR_PADRAO_MERCADO, PROVEDOR_PADRAO_CRIPTO):
        return True

    limpo = (simbolo or "").strip().upper()
    if not limpo:
        return False

    fontes = {f.upper() for f, _ in provedor.fontes}
    if limpo in fontes:
        return True

    foco = provedor.regiao_foco
    if foco == "Brasil":
        return limpo.endswith(".SA")
    if foco == "EUA":
        return not limpo.endswith(".SA") and "-USD" not in limpo
    if foco == "Cripto":
        return limpo.endswith("-USD")
    if foco in ("Europa", "Asia"):
        return limpo in fontes
    return True
