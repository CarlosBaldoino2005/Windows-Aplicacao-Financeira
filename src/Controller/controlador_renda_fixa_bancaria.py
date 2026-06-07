"""Coordena hubs de LCI/LCA e CDB."""
from __future__ import annotations

from src.Model.oferta_renda_fixa_bancaria import ResultadoConsultaOfertas
from src.Model.renda_fixa_bancaria_informacoes import (
    IndicadorRendaFixa,
    InformacoesProdutoRendaFixa,
    obter_indicadores_gerais_renda_fixa,
    obter_informacoes_cdb,
    obter_informacoes_lca,
    obter_informacoes_lci,
)
from src.Model.simulacao_renda_fixa_bancaria import ResultadoSimulacaoRendaFixaBancaria
from src.Service.indicadores_mercado_servico import IndicadoresMercado, IndicadoresMercadoServico
from src.Service.meelion_renda_fixa_servico import MeelionRendaFixaServico
from src.Service.renda_fixa_bancaria_simulacao_servico import RendaFixaBancariaSimulacaoServico
from src.Tool.validadores import validar_valor_monetario_ptbr


class ControladorRendaFixaBancaria:
    """Expoe informacoes, indicadores BCB e simulacao para LCI, LCA e CDB."""

    def __init__(self) -> None:
        self._simulacao = RendaFixaBancariaSimulacaoServico()
        self._indicadores = IndicadoresMercadoServico()
        self._meelion = MeelionRendaFixaServico()

    def obter_distribuidores_ofertas(self) -> list[str]:
        return self._meelion.obter_distribuidores()

    def obter_opcoes_prazo_ofertas(self) -> list[tuple[str, str]]:
        return self._meelion.obter_opcoes_prazo()

    def buscar_ofertas(
        self,
        modo: str,
        distribuidor: str,
        prazo_slug: str | None = None,
        apenas_emissor_igual_distribuidor: bool = False,
    ) -> tuple[ResultadoConsultaOfertas | None, str | None]:
        tipos = "LCI,LCA" if modo == "lci_lca" else "CDB"
        return self._meelion.buscar_ofertas(
            tipos_investimento=tipos,
            distribuidor=distribuidor,
            prazo_slug=prazo_slug,
            apenas_emissor_igual_distribuidor=apenas_emissor_igual_distribuidor,
        )

    def obter_informacoes_lci(self) -> InformacoesProdutoRendaFixa:
        return obter_informacoes_lci()

    def obter_informacoes_lca(self) -> InformacoesProdutoRendaFixa:
        return obter_informacoes_lca()

    def obter_informacoes_cdb(self) -> InformacoesProdutoRendaFixa:
        return obter_informacoes_cdb()

    def obter_indicadores_gerais(self) -> list[IndicadorRendaFixa]:
        return obter_indicadores_gerais_renda_fixa()

    def obter_indicadores_mercado(self) -> IndicadoresMercado:
        return self._indicadores.obter_indicadores()

    def simular(
        self,
        produto: str,
        valor_texto: str,
        prazo_dias_texto: str,
        modalidade: str,
        percentual_cdi_texto: str | None = None,
        taxa_prefixada_texto: str | None = None,
    ) -> tuple[ResultadoSimulacaoRendaFixaBancaria | None, str | None]:
        valor, erro_valor = validar_valor_monetario_ptbr(valor_texto)
        if erro_valor:
            return None, erro_valor

        prazo, erro_prazo = _validar_prazo_dias(prazo_dias_texto)
        if erro_prazo:
            return None, erro_prazo

        pct_cdi = None
        taxa_prefix = None
        modalidade_norm = (modalidade or "").strip().lower()

        if modalidade_norm == "cdi":
            pct_cdi, erro_pct = _validar_percentual(percentual_cdi_texto or "")
            if erro_pct:
                return None, erro_pct
        elif modalidade_norm == "prefixado":
            taxa_prefix, erro_taxa = _validar_taxa_aa(taxa_prefixada_texto or "")
            if erro_taxa:
                return None, erro_taxa
        else:
            return None, "Escolha rentabilidade atrelada ao CDI ou prefixada."

        return self._simulacao.simular(
            produto=produto,
            valor_inicial=valor,
            prazo_dias=prazo,
            modalidade=modalidade_norm,
            percentual_cdi=pct_cdi,
            taxa_prefixada_aa=taxa_prefix,
        )


def _validar_prazo_dias(texto: str) -> tuple[int | None, str | None]:
    if not texto or not str(texto).strip():
        return None, "Informe o prazo em dias (ex.: 365)."
    limpo = str(texto).strip().replace(".", "")
    if not limpo.isdigit():
        return None, "Prazo invalido. Use apenas numeros inteiros (dias)."
    valor = int(limpo)
    if valor < 1:
        return None, "Informe um prazo de pelo menos 1 dia."
    if valor > 3650:
        return None, "Informe um prazo de no maximo 3.650 dias."
    return valor, None


def _validar_percentual(texto: str) -> tuple[float | None, str | None]:
    if not texto or not str(texto).strip():
        return None, "Informe o percentual do CDI (ex.: 100)."
    limpo = str(texto).strip().replace("%", "").replace(",", ".")
    try:
        valor = float(limpo)
    except ValueError:
        return None, "Percentual do CDI invalido. Ex.: 95 ou 100."
    if valor <= 0 or valor > 300:
        return None, "Informe um percentual do CDI entre 0,01 e 300."
    return valor, None


def _validar_taxa_aa(texto: str) -> tuple[float | None, str | None]:
    if not texto or not str(texto).strip():
        return None, "Informe a taxa prefixada anual (ex.: 12,5)."
    limpo = str(texto).strip().replace("%", "").replace(",", ".")
    try:
        valor = float(limpo)
    except ValueError:
        return None, "Taxa prefixada invalida. Ex.: 12,5."
    if valor <= 0 or valor > 50:
        return None, "Informe uma taxa prefixada entre 0,01 e 50% a.a."
    return valor, None
