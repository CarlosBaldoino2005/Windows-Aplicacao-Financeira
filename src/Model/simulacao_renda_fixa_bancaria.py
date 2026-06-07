"""Resultado da simulacao de LCI, LCA ou CDB."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResultadoSimulacaoRendaFixaBancaria:
    produto: str
    modalidade: str
    taxa_rotulo: str
    valor_inicial: float
    dias_periodo: int
    data_inicio_texto: str
    data_fim_texto: str

    valor_bruto_produto: float
    rendimento_bruto_produto: float
    iof_produto: float
    aliquota_ir_produto: float
    imposto_ir_produto: float
    valor_liquido_produto: float
    rendimento_liquido_produto: float
    rendimento_liquido_produto_pct: float

    valor_bruto_cdi: float | None = None
    rendimento_bruto_cdi: float | None = None
    aliquota_ir_cdi: float | None = None
    imposto_ir_cdi: float | None = None
    valor_liquido_cdi: float | None = None
    rendimento_liquido_cdi: float | None = None
    rendimento_liquido_cdi_pct: float | None = None

    diferenca_liquida_vs_cdi: float | None = None
    cdi_aa_referencia: float | None = None
    observacoes: list[str] = field(default_factory=list)
    aviso: str = ""
