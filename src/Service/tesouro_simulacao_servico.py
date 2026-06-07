"""Simulacao educativa de investimento em titulos do Tesouro Direto."""
from __future__ import annotations

from datetime import date, datetime

from src.Model.simulacao_tesouro import ResultadoSimulacaoTesouro
from src.Model.titulo_tesouro import TituloTesouro
from src.Service.cdi_servico import CdiServico
from src.Service.provedores.util_provedor import requisicao_json
from src.Tool.imposto_renda_fixa_helper import (
    calcular_imposto_renda,
    calcular_iof_sobre_rendimento,
)
from src.Tool.registrador_log import RegistradorLog

TAXA_CUSTODIA_AA = 0.002  # 0,20% ao ano
CODIGO_SERIE_IPCA_12M = 433
CODIGO_SERIE_IGPM_12M = 11427
URL_SERIE_BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

FAMILIAS_IPCA = frozenset({"IPCA+", "IPCA+ com juros", "Educa+", "Renda+"})
FAMILIAS_IGPM = frozenset({"IGPM+ com juros"})
FAMILIAS_RENDA_MENSAL = frozenset({"Educa+", "Renda+"})


class TesouroSimulacaoServico:
    """Estima valor no vencimento, impostos e comparacao com 100% CDI."""

    def __init__(self) -> None:
        self._cdi = CdiServico()
        self._log = RegistradorLog()
        self._cache_indice: dict[int, float | None] = {}

    def simular(
        self,
        titulo: TituloTesouro,
        valor_inicial: float,
        data_aplicacao: date | None = None,
    ) -> tuple[ResultadoSimulacaoTesouro | None, str | None]:
        if valor_inicial <= 0:
            return None, "Informe um valor maior que zero."

        if titulo.taxa_venda is None or titulo.taxa_venda <= 0:
            return None, "Taxa de venda indisponivel para simular este titulo."

        hoje = date.today()
        data_inicio = data_aplicacao or hoje
        data_fim = titulo.data_vencimento

        if data_fim <= data_inicio:
            return None, "Este titulo ja venceu ou vence hoje. Escolha outro vencimento."

        dias = (data_fim - data_inicio).days
        if dias <= 0:
            return None, "Periodo invalido para simulacao."

        anos = dias / 365.25
        observacoes: list[str] = []
        ipca_aa: float | None = None
        igpm_aa: float | None = None
        taxa_real = titulo.taxa_venda

        if titulo.familia in FAMILIAS_IPCA:
            ipca_aa = self._obter_ultimo_indice_anual(CODIGO_SERIE_IPCA_12M)
            if ipca_aa is None:
                ipca_aa = 4.5
                observacoes.append(
                    "IPCA projetado: 4,50% a.a. (estimativa padrao; nao foi possivel consultar o BCB)."
                )
            else:
                observacoes.append(
                    f"IPCA projetado: {ipca_aa:.2f}% a.a. (ultimo IPCA acumulado 12 meses — BCB)."
                )
            taxa_rotulo = f"IPCA + {taxa_real:.2f}% a.a."
            fator = (1.0 + taxa_real / 100.0) ** anos * (1.0 + ipca_aa / 100.0) ** anos
        elif titulo.familia in FAMILIAS_IGPM:
            igpm_aa = self._obter_ultimo_indice_anual(CODIGO_SERIE_IGPM_12M)
            if igpm_aa is None:
                igpm_aa = 4.0
                observacoes.append(
                    "IGP-M projetado: 4,00% a.a. (estimativa padrao; nao foi possivel consultar o BCB)."
                )
            else:
                observacoes.append(
                    f"IGP-M projetado: {igpm_aa:.2f}% a.a. (ultimo IGP-M acumulado 12 meses — BCB)."
                )
            taxa_rotulo = f"IGP-M + {taxa_real:.2f}% a.a."
            fator = (1.0 + taxa_real / 100.0) ** anos * (1.0 + igpm_aa / 100.0) ** anos
        else:
            taxa_rotulo = f"{taxa_real:.2f}% a.a."
            fator = (1.0 + taxa_real / 100.0) ** anos
            if titulo.familia == "Selic":
                observacoes.append(
                    "Tesouro Selic e pos-fixado: simulacao usa a taxa da cotacao atual como referencia."
                )

        if titulo.familia in FAMILIAS_RENDA_MENSAL:
            observacoes.append(
                "Educa+ e Renda+ pagam renda mensal apos a conversao. "
                "O valor abaixo estima o saldo na data de vencimento/conversao (fase de acumulacao)."
            )

        if "juros" in titulo.familia.lower():
            observacoes.append(
                "Titulos com cupons semestrais: a simulacao considera reinvestimento implicito "
                "até o vencimento (taxa indicativa da cotacao)."
            )

        valor_bruto = round(valor_inicial * fator, 2)
        rendimento_bruto = round(valor_bruto - valor_inicial, 2)
        custodia = round(valor_inicial * TAXA_CUSTODIA_AA * anos, 2)

        rendimento_apos_custodia = max(0.0, rendimento_bruto - custodia)
        iof = calcular_iof_sobre_rendimento(rendimento_apos_custodia, dias)
        base_ir = max(0.0, rendimento_apos_custodia - iof)
        ir, aliquota_ir = calcular_imposto_renda(base_ir, dias)
        valor_liquido = round(valor_bruto - custodia - iof - ir, 2)
        rendimento_liquido = round(valor_liquido - valor_inicial, 2)
        rendimento_liq_pct = round((valor_liquido / valor_inicial - 1.0) * 100.0, 2)

        data_inicio_txt = data_inicio.strftime("%d/%m/%Y")
        data_fim_txt = data_fim.strftime("%d/%m/%Y")

        resultado_cdi = self._cdi.calcular_rendimento_ate_vencimento(
            valor_inicial,
            data_inicio_txt,
            data_fim_txt,
        )
        valor_bruto_cdi = None
        rendimento_cdi = None
        ir_cdi = None
        aliquota_cdi = None
        liquido_cdi = None
        rendimento_liq_cdi = None
        rendimento_liq_cdi_pct = None
        diferenca = None

        if resultado_cdi:
            valor_bruto_cdi = resultado_cdi["valor_fim"]
            rendimento_cdi = resultado_cdi["rendimento"]
            if resultado_cdi.get("projecao_futura"):
                observacoes.append(
                    "CDI: historico do BCB ate hoje + projecao da media recente ate o vencimento."
                )
            ir_cdi, aliquota_cdi = calcular_imposto_renda(rendimento_cdi, dias)
            liquido_cdi = round(valor_bruto_cdi - ir_cdi, 2)
            rendimento_liq_cdi = round(liquido_cdi - valor_inicial, 2)
            rendimento_liq_cdi_pct = round((liquido_cdi / valor_inicial - 1.0) * 100.0, 2)
            diferenca = round(rendimento_liquido - rendimento_liq_cdi, 2)
        else:
            observacoes.append(
                "Comparacao com CDI indisponivel (falha ao consultar taxas diarias no Banco Central)."
            )

        aviso = (
            "Simulacao educativa com taxa da cotacao atual, IPCA/IGP-M projetados e IR regressivo. "
            "Nao considera venda antecipada (marcacao a mercado), IOF apos 30 dias e isencoes de custodia. "
            "Nao e recomendacao de investimento."
        )

        return (
            ResultadoSimulacaoTesouro(
                valor_inicial=round(valor_inicial, 2),
                dias_periodo=dias,
                data_inicio_texto=data_inicio_txt,
                data_fim_texto=data_fim_txt,
                taxa_tesouro_aa=taxa_real,
                taxa_tesouro_rotulo=taxa_rotulo,
                valor_bruto_tesouro=valor_bruto,
                rendimento_bruto_tesouro=rendimento_bruto,
                taxa_custodia_estimada=custodia,
                iof_tesouro=iof,
                aliquota_ir_tesouro=aliquota_ir,
                imposto_ir_tesouro=ir,
                valor_liquido_tesouro=valor_liquido,
                rendimento_liquido_tesouro=rendimento_liquido,
                rendimento_liquido_tesouro_pct=rendimento_liq_pct,
                valor_bruto_cdi=valor_bruto_cdi,
                rendimento_bruto_cdi=rendimento_cdi,
                aliquota_ir_cdi=aliquota_cdi,
                imposto_ir_cdi=ir_cdi,
                valor_liquido_cdi=liquido_cdi,
                rendimento_liquido_cdi=rendimento_liq_cdi,
                rendimento_liquido_cdi_pct=rendimento_liq_cdi_pct,
                diferenca_liquida_vs_cdi=diferenca,
                ipca_projetada_aa=ipca_aa,
                igpm_projetado_aa=igpm_aa,
                observacoes=observacoes,
                aviso=aviso,
            ),
            None,
        )

    def _obter_ultimo_indice_anual(self, codigo_serie: int) -> float | None:
        if codigo_serie in self._cache_indice:
            return self._cache_indice[codigo_serie]

        hoje = date.today()
        inicio = date(hoje.year - 2, hoje.month, 1)
        url = (
            URL_SERIE_BCB.format(codigo=codigo_serie)
            + f"?formato=json&dataInicial={inicio.strftime('%d/%m/%Y')}"
            + f"&dataFinal={hoje.strftime('%d/%m/%Y')}"
        )
        dados = requisicao_json(url, log=self._log)
        if not isinstance(dados, list) or not dados:
            self._cache_indice[codigo_serie] = None
            return None

        ultimo = dados[-1]
        if not isinstance(ultimo, dict):
            self._cache_indice[codigo_serie] = None
            return None
        try:
            valor = float(str(ultimo.get("valor", "")).replace(",", "."))
        except (TypeError, ValueError):
            self._cache_indice[codigo_serie] = None
            return None

        self._cache_indice[codigo_serie] = valor
        return valor
