"""URLs oficiais do site Tesouro Direto por tipo/familia de titulo."""
from __future__ import annotations

from src.Model.tesouro_informacoes import obter_familia_por_tipo

URL_BASE_TESOURO = "https://www.tesourodireto.com.br"
URL_PADRAO_TESOURO = f"{URL_BASE_TESOURO}/"

MAPA_URL_POR_TIPO: dict[str, str] = {
    "Tesouro Selic": f"{URL_BASE_TESOURO}/produtos/titulos/selic",
    "Tesouro Prefixado": f"{URL_BASE_TESOURO}/produtos/titulos/prefixado",
    "Tesouro Prefixado com Juros Semestrais": f"{URL_BASE_TESOURO}/produtos/titulos/prefixado",
    "Tesouro IPCA+": f"{URL_BASE_TESOURO}/produtos/titulos/ipca-mais",
    "Tesouro IPCA+ com Juros Semestrais": f"{URL_BASE_TESOURO}/produtos/titulos/ipca-mais",
    "Tesouro IGPM+ com Juros Semestrais": f"{URL_BASE_TESOURO}/titulos/historico-de-precos-e-taxas.htm",
    "Tesouro Educa+": f"{URL_BASE_TESOURO}/produtos/titulos/educa-mais",
    "Tesouro Renda+ Aposentadoria Extra": f"{URL_BASE_TESOURO}/produtos/titulos/renda-mais",
}

MAPA_URL_POR_FAMILIA: dict[str, str] = {
    "Selic": f"{URL_BASE_TESOURO}/produtos/titulos/selic",
    "Prefixado": f"{URL_BASE_TESOURO}/produtos/titulos/prefixado",
    "Prefixado com juros": f"{URL_BASE_TESOURO}/produtos/titulos/prefixado",
    "IPCA+": f"{URL_BASE_TESOURO}/produtos/titulos/ipca-mais",
    "IPCA+ com juros": f"{URL_BASE_TESOURO}/produtos/titulos/ipca-mais",
    "IGPM+ com juros": f"{URL_BASE_TESOURO}/titulos/historico-de-precos-e-taxas.htm",
    "Educa+": f"{URL_BASE_TESOURO}/produtos/titulos/educa-mais",
    "Renda+": f"{URL_BASE_TESOURO}/produtos/titulos/renda-mais",
}


def obter_url_site_tesouro(tipo_titulo: str, data_vencimento_texto: str = "") -> str:
    """
    Retorna a pagina oficial do Tesouro Direto para a familia do titulo.
    O vencimento e usado apenas no rotulo; a pagina do produto permite simular o ano.
    """
    tipo = (tipo_titulo or "").strip()
    if tipo in MAPA_URL_POR_TIPO:
        return MAPA_URL_POR_TIPO[tipo]

    familia = obter_familia_por_tipo(tipo)
    if familia in MAPA_URL_POR_FAMILIA:
        return MAPA_URL_POR_FAMILIA[familia]

    return URL_PADRAO_TESOURO


def obter_rotulo_botao_site_tesouro(familia: str, data_vencimento_texto: str = "") -> str:
    """Texto do botao conforme a familia exibida na tela."""
    familia = (familia or "Tesouro").strip()
    ano = _extrair_ano_vencimento(data_vencimento_texto)
    if ano:
        return f"Abrir {familia} {ano} no Tesouro Direto"
    return f"Abrir {familia} no Tesouro Direto"


def _extrair_ano_vencimento(data_vencimento_texto: str) -> str:
    texto = (data_vencimento_texto or "").strip()
    if len(texto) >= 4 and texto[-4:].isdigit():
        return texto[-4:]
    return ""
