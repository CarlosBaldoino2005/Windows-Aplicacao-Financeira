"""Simulacao educativa de LCI, LCA e CDB com comparacao ao CDI."""
from __future__ import annotations

from datetime import date, timedelta

from src.Model.simulacao_renda_fixa_bancaria import ResultadoSimulacaoRendaFixaBancaria
from src.Service.cdi_servico import CdiServico
from src.Tool.imposto_renda_fixa_helper import (
    calcular_imposto_renda,
    calcular_iof_sobre_rendimento,
)

PRODUTOS_ISENTOS_IR = frozenset({"LCI", "LCA"})
MODALIDADE_CDI = "cdi"
MODALIDADE_PREFIXADO = "prefixado"


class RendaFixaBancariaSimulacaoServico:
    """Simula rendimento, impostos e compara com 100% CDI no mesmo prazo."""

    def __init__(self) -> None:
        self._cdi = CdiServico()

    def simular(
        self,
        produto: str,
        valor_inicial: float,
        prazo_dias: int,
        modalidade: str,
        percentual_cdi: float | None = None,
        taxa_prefixada_aa: float | None = None,
    ) -> tuple[ResultadoSimulacaoRendaFixaBancaria | None, str | None]:
        produto = (produto or "").strip().upper()
        if produto not in ("LCI", "LCA", "CDB"):
            return None, "Produto invalido. Use LCI, LCA ou CDB."

        if valor_inicial <= 0:
            return None, "Informe um valor maior que zero."

        if prazo_dias < 1:
            return None, "Informe um prazo de pelo menos 1 dia."
        if prazo_dias > 3650:
            return None, "Informe um prazo de no maximo 3.650 dias (10 anos)."

        modalidade = (modalidade or "").strip().lower()
        if modalidade not in (MODALIDADE_CDI, MODALIDADE_PREFIXADO):
            return None, "Modalidade invalida. Use CDI ou prefixado."

        hoje = date.today()
        data_fim = hoje + timedelta(days=prazo_dias)
        data_inicio_txt = hoje.strftime("%d/%m/%Y")
        data_fim_txt = data_fim.strftime("%d/%m/%Y")
        observacoes: list[str] = []

        if modalidade == MODALIDADE_CDI:
            if percentual_cdi is None or percentual_cdi <= 0:
                return None, "Informe o percentual do CDI (ex.: 100 para 100% CDI)."
            if percentual_cdi > 300:
                return None, "Percentual do CDI muito alto. Informe um valor ate 300%."

            mult = percentual_cdi / 100.0
            taxa_rotulo = f"{percentual_cdi:.2f}% do CDI"
            resultado_produto = self._cdi.calcular_rendimento_ate_vencimento(
                valor_inicial,
                data_inicio_txt,
                data_fim_txt,
                multiplicador_cdi=mult,
            )
            if resultado_produto is None:
                return None, "Nao foi possivel calcular o rendimento com base no CDI (BCB)."

            valor_bruto = resultado_produto["valor_fim"]
            rendimento_bruto = resultado_produto["rendimento"]
            if resultado_produto.get("projecao_futura"):
                observacoes.append(
                    "CDI: historico do BCB ate hoje + projecao da media recente ate o vencimento."
                )
        else:
            if taxa_prefixada_aa is None or taxa_prefixada_aa <= 0:
                return None, "Informe a taxa prefixada anual (ex.: 12,5)."
            if taxa_prefixada_aa > 50:
                return None, "Taxa prefixada invalida. Informe um valor ate 50% a.a."

            anos = prazo_dias / 365.25
            fator = (1.0 + taxa_prefixada_aa / 100.0) ** anos
            valor_bruto = round(valor_inicial * fator, 2)
            rendimento_bruto = round(valor_bruto - valor_inicial, 2)
            taxa_rotulo = f"{taxa_prefixada_aa:.2f}% a.a. (prefixado)"
            observacoes.append(
                "Taxa prefixada: juros compostos ate o vencimento, sem alteracao de taxa no periodo."
            )

        iof = calcular_iof_sobre_rendimento(rendimento_bruto, prazo_dias)
        base_ir = max(0.0, rendimento_bruto - iof)

        if produto in PRODUTOS_ISENTOS_IR:
            ir = 0.0
            aliquota_ir = 0.0
            observacoes.append(f"{produto} isento de IR para pessoa fisica.")
        else:
            ir, aliquota_ir = calcular_imposto_renda(base_ir, prazo_dias)

        valor_liquido = round(valor_bruto - iof - ir, 2)
        rendimento_liquido = round(valor_liquido - valor_inicial, 2)
        rendimento_liq_pct = round((valor_liquido / valor_inicial - 1.0) * 100.0, 2)

        resultado_cdi = self._cdi.calcular_rendimento_ate_vencimento(
            valor_inicial,
            data_inicio_txt,
            data_fim_txt,
            multiplicador_cdi=1.0,
        )
        cdi_aa = self._cdi.obter_cdi_anualizado_estimado()

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
            ir_cdi, aliquota_cdi = calcular_imposto_renda(rendimento_cdi, prazo_dias)
            liquido_cdi = round(valor_bruto_cdi - ir_cdi, 2)
            rendimento_liq_cdi = round(liquido_cdi - valor_inicial, 2)
            rendimento_liq_cdi_pct = round((liquido_cdi / valor_inicial - 1.0) * 100.0, 2)
            diferenca = round(rendimento_liquido - rendimento_liq_cdi, 2)
        else:
            observacoes.append("Comparacao com 100% CDI indisponivel no momento.")

        aviso = (
            "Simulacao educativa com taxas informadas por voce e CDI do Banco Central. "
            "Ofertas reais variam por banco, carencia e liquidez. Nao e recomendacao de investimento."
        )

        return (
            ResultadoSimulacaoRendaFixaBancaria(
                produto=produto,
                modalidade=modalidade,
                taxa_rotulo=taxa_rotulo,
                valor_inicial=round(valor_inicial, 2),
                dias_periodo=prazo_dias,
                data_inicio_texto=data_inicio_txt,
                data_fim_texto=data_fim_txt,
                valor_bruto_produto=valor_bruto,
                rendimento_bruto_produto=rendimento_bruto,
                iof_produto=iof,
                aliquota_ir_produto=aliquota_ir,
                imposto_ir_produto=ir,
                valor_liquido_produto=valor_liquido,
                rendimento_liquido_produto=rendimento_liquido,
                rendimento_liquido_produto_pct=rendimento_liq_pct,
                valor_bruto_cdi=valor_bruto_cdi,
                rendimento_bruto_cdi=rendimento_cdi,
                aliquota_ir_cdi=aliquota_cdi,
                imposto_ir_cdi=ir_cdi,
                valor_liquido_cdi=liquido_cdi,
                rendimento_liquido_cdi=rendimento_liq_cdi,
                rendimento_liquido_cdi_pct=rendimento_liq_cdi_pct,
                diferenca_liquida_vs_cdi=diferenca,
                cdi_aa_referencia=cdi_aa,
                observacoes=observacoes,
                aviso=aviso,
            ),
            None,
        )
