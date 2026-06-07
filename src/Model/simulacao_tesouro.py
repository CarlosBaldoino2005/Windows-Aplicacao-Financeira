"""Resultado da simulacao de investimento em titulo do Tesouro Direto."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResultadoSimulacaoTesouro:
    """Comparativo Tesouro x CDI com impostos estimados."""

    valor_inicial: float
    dias_periodo: int
    data_inicio_texto: str
    data_fim_texto: str
    taxa_tesouro_aa: float
    taxa_tesouro_rotulo: str

    valor_bruto_tesouro: float
    rendimento_bruto_tesouro: float
    taxa_custodia_estimada: float
    iof_tesouro: float
    aliquota_ir_tesouro: float
    imposto_ir_tesouro: float
    valor_liquido_tesouro: float
    rendimento_liquido_tesouro: float
    rendimento_liquido_tesouro_pct: float

    valor_bruto_cdi: float | None = None
    rendimento_bruto_cdi: float | None = None
    aliquota_ir_cdi: float | None = None
    imposto_ir_cdi: float | None = None
    valor_liquido_cdi: float | None = None
    rendimento_liquido_cdi: float | None = None
    rendimento_liquido_cdi_pct: float | None = None

    diferenca_liquida_vs_cdi: float | None = None
    ipca_projetada_aa: float | None = None
    igpm_projetado_aa: float | None = None
    observacoes: list[str] = field(default_factory=list)
    aviso: str = ""
