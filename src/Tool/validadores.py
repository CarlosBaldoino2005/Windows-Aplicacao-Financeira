"""Validadores reutilizaveis para entradas da API e da interface."""
import re
from datetime import datetime

from src.Model.acoes_universo import QUANTIDADE_PADRAO_PAINEL
from src.Tool.texto_busca_helper import normalizar_texto_busca


_FORMATO_DATA = "%d/%m/%Y"
_PADRAO_SIMBOLO = re.compile(r"^[A-Za-z0-9.\-^]{1,20}$")


_ALIASES_CRIPTO: dict[str, str] = {
    "BITCOIN": "BTC-USD",
    "BTC": "BTC-USD",
    "ETHEREUM": "ETH-USD",
    "ETH": "ETH-USD",
    "SOLANA": "SOL-USD",
    "SOL": "SOL-USD",
    "DOGECOIN": "DOGE-USD",
    "DOGE": "DOGE-USD",
    "RIPPLE": "XRP-USD",
    "XRP": "XRP-USD",
    "CARDANO": "ADA-USD",
    "ADA": "ADA-USD",
    "POLYGON": "POL-USD",
    "MATIC": "MATIC-USD",
    "POL": "POL-USD",
}

_ALIASES_CRIPTO_NORM: dict[str, str] = {
    normalizar_texto_busca(chave).upper(): valor
    for chave, valor in _ALIASES_CRIPTO.items()
}


def normalizar_simbolo_cripto(simbolo: str) -> tuple[str | None, str | None]:
    """
    Valida e normaliza par de cripto (ex.: BTC -> BTC-USD).
    Retorna (simbolo_ok, mensagem_erro).
    """
    if not simbolo or not simbolo.strip():
        return None, "Informe o codigo da cripto (ex.: BTC ou ETH-USD)."

    limpo = (
        normalizar_texto_busca(simbolo.strip())
        .upper()
        .replace("/", "-")
        .replace(" ", "")
    )
    if not _PADRAO_SIMBOLO.match(limpo):
        return None, "Codigo invalido. Use letras, numeros e hifen."

    if limpo in _ALIASES_CRIPTO_NORM:
        return _ALIASES_CRIPTO_NORM[limpo], None

    if "-USD" in limpo or "-USDT" in limpo:
        return limpo, None

    if re.match(r"^[A-Z0-9]{2,12}$", limpo):
        return f"{limpo}-USD", None

    return None, "Codigo de cripto invalido. Ex.: BTC, ETH-USD, SOL."


def normalizar_simbolo(simbolo: str) -> tuple[str | None, str | None]:
    """
    Valida e normaliza ticker (ex.: PETR4 -> PETR4.SA para B3).
    Retorna (simbolo_ok, mensagem_erro).
    """
    if not simbolo or not simbolo.strip():
        return None, "Informe o codigo da acao (ex.: PETR4 ou AAPL)."

    limpo = normalizar_texto_busca(simbolo.strip()).upper()
    if not _PADRAO_SIMBOLO.match(limpo):
        return None, "Codigo invalido. Use apenas letras, numeros e ponto."

    # Acoes brasileiras sem sufixo recebem .SA automaticamente.
    if "." not in limpo and re.match(r"^[A-Z]{4}\d{1,2}$", limpo):
        limpo = f"{limpo}.SA"

    return limpo, None


def validar_data_ptbr(texto: str) -> tuple[datetime | None, str | None]:
    """Valida data no formato dd/mm/aaaa."""
    if not texto or not texto.strip():
        return None, "Informe a data no formato dd/mm/aaaa."

    try:
        data = datetime.strptime(texto.strip(), _FORMATO_DATA)
    except ValueError:
        return None, "Data invalida. Use o formato dd/mm/aaaa (ex.: 02/06/2026)."

    return data, None


def validar_fotos_noticias(texto: str) -> tuple[str, str | None]:
    """Valida tamanho das fotos nas noticias: nenhum, pequeno, medio ou grande."""
    from src.Model.opcoes_fotos_noticias import (
        FOTOS_GRANDE,
        FOTOS_MEDIO,
        FOTOS_NENHUM,
        FOTOS_PADRAO,
        FOTOS_PEQUENO,
    )

    if not texto or not str(texto).strip():
        return FOTOS_PADRAO, None

    limpo = str(texto).strip().lower()
    mapa = {
        "nenhum": FOTOS_NENHUM,
        "nao": FOTOS_NENHUM,
        "não": FOTOS_NENHUM,
        "off": FOTOS_NENHUM,
        "pequeno": FOTOS_PEQUENO,
        "pequena": FOTOS_PEQUENO,
        "medio": FOTOS_MEDIO,
        "médio": FOTOS_MEDIO,
        "media": FOTOS_MEDIO,
        "grande": FOTOS_GRANDE,
    }
    if limpo in mapa:
        return mapa[limpo], None
    return (
        FOTOS_PADRAO,
        "Valor invalido para fotos_noticias. Use: nenhum, pequeno, medio ou grande.",
    )


def validar_fonte_grid(texto: str) -> tuple[str, str | None]:
    """Valida tamanho da fonte das grids: pequeno, medio ou grande."""
    from src.Model.opcoes_fonte_grid import (
        FONTE_GRANDE,
        FONTE_GRID_PADRAO,
        FONTE_MEDIO,
        FONTE_PEQUENO,
    )

    if not texto or not str(texto).strip():
        return FONTE_GRID_PADRAO, None

    limpo = str(texto).strip().lower()
    mapa = {
        "pequeno": FONTE_PEQUENO,
        "pequena": FONTE_PEQUENO,
        "medio": FONTE_MEDIO,
        "médio": FONTE_MEDIO,
        "media": FONTE_MEDIO,
        "grande": FONTE_GRANDE,
    }
    if limpo in mapa:
        return mapa[limpo], None
    return (
        FONTE_GRID_PADRAO,
        "Valor invalido para fonte_grid. Use: pequeno, medio ou grande.",
    )


def validar_modo_aparencia(texto: str) -> tuple[str, str | None]:
    """Valida modo claro ou escuro para o INI."""
    from src.View.tema import normalizar_modo_aparencia

    if not texto or not str(texto).strip():
        return normalizar_modo_aparencia("claro"), None
    limpo = str(texto).strip().lower()
    if limpo in ("claro", "light", "escuro", "dark"):
        return normalizar_modo_aparencia(limpo), None
    return (
        "claro",
        "Modo de aparencia invalido. Use claro ou escuro.",
    )


def validar_lista_simbolos(simbolos: list[str], maximo: int = 6) -> tuple[list[str], str | None]:
    """Valida lista de tickers para comparacao."""
    if not simbolos:
        return [], "Selecione ao menos duas acoes para comparar."

    normalizados: list[str] = []
    for item in simbolos:
        ok, erro = normalizar_simbolo(item)
        if erro:
            return [], erro
        if ok and ok not in normalizados:
            normalizados.append(ok)

    if len(normalizados) < 2:
        return [], "Informe pelo menos duas acoes diferentes para comparar."

    if len(normalizados) > maximo:
        return [], f"Maximo de {maximo} acoes por comparacao."

    return normalizados, None


def validar_lista_simbolos_cripto(
    simbolos: list[str], maximo: int = 6
) -> tuple[list[str], str | None]:
    """Valida lista de pares para comparacao de criptomoedas."""
    if not simbolos:
        return [], "Selecione ao menos duas criptomoedas para comparar."

    normalizados: list[str] = []
    for item in simbolos:
        ok, erro = normalizar_simbolo_cripto(item)
        if erro:
            return [], erro
        if ok and ok not in normalizados:
            normalizados.append(ok)

    if len(normalizados) < 2:
        return [], "Informe pelo menos duas criptos diferentes para comparar."

    if len(normalizados) > maximo:
        return [], f"Maximo de {maximo} criptos por comparacao."

    return normalizados, None


def validar_quantidade_cripto(
    texto: str,
    padrao: int = 15,
    minimo: int = 1,
    maximo: int = 80,
) -> tuple[int | None, str | None]:
    """Valida quantidade de criptos listadas no painel."""
    return validar_quantidade_acoes(texto, padrao=padrao, minimo=minimo, maximo=maximo)


def validar_quantidade_acoes(
    texto: str,
    padrao: int = QUANTIDADE_PADRAO_PAINEL,
    minimo: int = 1,
    maximo: int = 100,
) -> tuple[int | None, str | None]:
    """Valida quantidade de acoes exibidas no painel (numero inteiro)."""
    if not texto or not str(texto).strip():
        return padrao, None

    limpo = str(texto).strip()
    if not limpo.isdigit():
        return None, "Informe apenas numeros na quantidade de acoes."

    valor = int(limpo)
    if valor < minimo:
        return None, f"A quantidade minima e {minimo} acao."

    if valor > maximo:
        return None, f"A quantidade maxima e {maximo} acoes."

    return valor, None


def validar_quantidade_cotas(
    texto: str,
    padrao: int = 100,
    minimo: int = 1,
    maximo: int = 9_999_999,
) -> tuple[int | None, str | None]:
    """Valida quantidade de acoes/cotas para simulacao de investimento no grafico."""
    if not texto or not str(texto).strip():
        return padrao, None

    limpo = str(texto).strip().replace(".", "").replace(",", "")
    if not limpo.isdigit():
        return None, "Informe apenas numeros na quantidade de acoes."

    valor = int(limpo)
    if valor < minimo:
        return None, f"A quantidade minima e {minimo} acao."

    if valor > maximo:
        return None, "Informe no maximo {maximo:,} acoes.".replace(",", ".")

    return valor, None


def validar_sim_nao_config(
    texto: str,
    padrao: bool = False,
) -> tuple[bool, str | None]:
    """Interpreta sim/nao para opcoes do painel.ini."""
    if not texto or not str(texto).strip():
        return padrao, None

    limpo = str(texto).strip().lower()
    if limpo in ("sim", "s", "1", "true", "verdadeiro", "ligado", "on"):
        return True, None
    if limpo in ("nao", "não", "n", "0", "false", "falso", "desligado", "off"):
        return False, None
    return padrao, "Informe Sim ou Nao."


def validar_intervalo_atualizacao_segundos(
    texto: str,
    padrao: int = 60,
    minimo: int = 10,
    maximo: int = 3600,
) -> tuple[int | None, str | None]:
    """Valida intervalo da atualizacao automatica (10 a 3600 segundos)."""
    if not texto or not str(texto).strip():
        return padrao, None

    limpo = str(texto).strip()
    if not limpo.isdigit():
        return None, "Informe apenas numeros no intervalo em segundos."

    valor = int(limpo)
    if valor < minimo:
        return None, f"O intervalo minimo e {minimo} segundos."
    if valor > maximo:
        return None, f"O intervalo maximo e {maximo} segundos."
    return valor, None


def validar_valor_monetario_opcional(texto: str) -> tuple[float | None, str | None]:
    """Valida valor monetario pt-BR ou aceita vazio."""
    if not texto or not str(texto).strip():
        return None, None
    return validar_valor_monetario_ptbr(texto)


def validar_limites_monitoramento(
    valor_baixo: float | None,
    valor_alto: float | None,
    preco_atual: float | None = None,
    moeda: str = "BRL",
) -> str | None:
    """Exige ao menos um limite, garante ordem entre limites e coerencia com o preco atual."""
    if valor_baixo is None and valor_alto is None:
        return "Informe pelo menos valor baixo ou valor alto."

    if valor_baixo is not None and valor_baixo <= 0:
        return "Valor baixo deve ser maior que zero."

    if valor_alto is not None and valor_alto <= 0:
        return "Valor alto deve ser maior que zero."

    if (
        valor_baixo is not None
        and valor_alto is not None
        and valor_baixo >= valor_alto
    ):
        return "Valor baixo deve ser menor que valor alto."

    if preco_atual is not None and preco_atual > 0:
        preco_texto = _formatar_preco_validacao(preco_atual, moeda)
        if valor_baixo is not None and valor_baixo > preco_atual:
            return (
                f"Valor baixo nao pode ser maior que o preco atual ({preco_texto})."
            )
        if valor_alto is not None and valor_alto < preco_atual:
            return (
                f"Valor alto nao pode ser menor que o preco atual ({preco_texto})."
            )

    return None


def _formatar_preco_validacao(valor: float, moeda: str = "BRL") -> str:
    """Formata preco para mensagens de validacao em pt-BR."""
    if moeda == "BRL":
        texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {texto}"
    return f"US$ {valor:,.2f}"


def validar_valor_monetario_ptbr(texto: str) -> tuple[float | None, str | None]:
    """Valida valor em reais/dolares no formato pt-BR (ex.: R$ 1.234,56)."""
    if not texto or not str(texto).strip():
        return None, "Informe o valor disponivel (ex.: R$ 10.000,00)."

    limpo = str(texto).strip().upper()
    limpo = limpo.replace("R$", "").replace("US$", "").replace("USD", "").strip()
    limpo = limpo.replace(" ", "")

    if not limpo:
        return None, "Informe o valor disponivel (ex.: R$ 10.000,00)."

    if "," in limpo and "." in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    elif "," in limpo:
        limpo = limpo.replace(",", ".")

    try:
        valor = float(limpo)
    except ValueError:
        return None, "Valor invalido. Use numeros no formato brasileiro (ex.: 1.234,56)."

    if valor <= 0:
        return None, "Informe um valor maior que zero."

    return valor, None


def validar_provedor_noticias(
    texto: str,
    categoria: str = "mercado",
) -> tuple[str, str | None]:
    """Valida chave do servidor de noticias (mercado ou cripto)."""
    from src.Model.provedores_noticias import (
        CATEGORIA_CRIPTO,
        PROVEDOR_PADRAO_CRIPTO,
        PROVEDOR_PADRAO_MERCADO,
        obter_provedor,
    )

    padrao = (
        PROVEDOR_PADRAO_CRIPTO
        if categoria == CATEGORIA_CRIPTO
        else PROVEDOR_PADRAO_MERCADO
    )
    if not texto or not str(texto).strip():
        return padrao, None

    chave = str(texto).strip().lower()
    if obter_provedor(chave, categoria):
        return chave, None
    return padrao, "Provedor de noticias invalido para esta categoria."
