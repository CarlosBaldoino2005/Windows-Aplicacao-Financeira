"""Posicoes da carteira de investimentos do usuario."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.Model.cotacao import CotacaoResumo
from src.Model.resultado_busca import ResultadoBusca

TipoAtivoCarteira = Literal["acoes", "cripto", "fiis", "indices"]

TIPOS_ATIVO_CARTEIRA: tuple[TipoAtivoCarteira, ...] = (
    "acoes",
    "cripto",
    "fiis",
    "indices",
)

ROTULOS_TIPO_CARTEIRA: dict[TipoAtivoCarteira, str] = {
    "acoes": "Acao",
    "cripto": "Criptomoeda",
    "fiis": "FII",
    "indices": "Indice",
}

MAXIMO_POSICOES_CARTEIRA = 200


@dataclass(frozen=True)
class ResultadoBuscaCarteira:
    """Item retornado na busca automatica de ativos para a carteira."""

    simbolo: str
    nome: str
    bolsa: str
    tipo_ativo: TipoAtivoCarteira

    @classmethod
    def de_resultado_busca(
        cls,
        item: ResultadoBusca,
        tipo_ativo: TipoAtivoCarteira,
    ) -> ResultadoBuscaCarteira:
        return cls(
            simbolo=item.simbolo,
            nome=item.nome,
            bolsa=item.bolsa,
            tipo_ativo=tipo_ativo,
        )


@dataclass(frozen=True)
class PosicaoCarteira:
    """Compra registrada pelo usuario."""

    id: str
    simbolo: str
    tipo_ativo: TipoAtivoCarteira
    quantidade: float
    preco_compra: float
    data_compra: str

    @property
    def valor_investido(self) -> float:
        return round(self.quantidade * self.preco_compra, 4)


@dataclass(frozen=True)
class LinhaCarteira:
    """Posicao com cotacao atual e dividendos calculados."""

    posicao: PosicaoCarteira
    cotacao: CotacaoResumo | None
    dividendos_recebidos: float = 0.0
    dividendo_previsto_proximo_mes: float | None = None
    proximo_dividendo_data: str = ""
    proximo_dividendo_valor_por_cota: float | None = None
    proximo_dividendo_previsto: float | None = None

    @property
    def preco_atual(self) -> float | None:
        if self.cotacao is None or self.cotacao.preco <= 0:
            return None
        return self.cotacao.preco

    @property
    def valor_atual(self) -> float | None:
        if self.preco_atual is None:
            return None
        return round(self.posicao.quantidade * self.preco_atual, 4)

    @property
    def resultado_reais(self) -> float | None:
        if self.valor_atual is None:
            return None
        return round(self.valor_atual - self.posicao.valor_investido, 4)

    @property
    def resultado_percentual(self) -> float | None:
        if self.resultado_reais is None or self.posicao.valor_investido <= 0:
            return None
        return round((self.resultado_reais / self.posicao.valor_investido) * 100, 2)


@dataclass(frozen=True)
class VendaCarteira:
    """Venda registrada pelo usuario com dados da operacao."""

    id: str
    posicao_id: str
    simbolo: str
    tipo_ativo: TipoAtivoCarteira
    quantidade: float
    preco_compra: float
    preco_venda: float
    data_compra: str
    data_venda: str
    dividendos_recebidos: float = 0.0

    @property
    def valor_compra(self) -> float:
        return round(self.quantidade * self.preco_compra, 4)

    @property
    def valor_venda(self) -> float:
        return round(self.quantidade * self.preco_venda, 4)

    @property
    def lucro_capital(self) -> float:
        return round(self.valor_venda - self.valor_compra, 4)

    @property
    def lucro_total(self) -> float:
        return round(self.lucro_capital + self.dividendos_recebidos, 4)

    @property
    def lucro_percentual(self) -> float | None:
        if self.valor_compra <= 0:
            return None
        return round((self.lucro_total / self.valor_compra) * 100, 2)


@dataclass(frozen=True)
class LinhaVendaCarteira:
    """Venda com nome do ativo e moeda para exibicao."""

    venda: VendaCarteira
    nome: str = ""
    moeda: str = "BRL"


def tipo_carteira_para_monitoramento(tipo: TipoAtivoCarteira) -> str:
    """Mapeia tipo da carteira para o monitoramento de precos."""
    if tipo == "cripto":
        return "cripto"
    if tipo == "fiis":
        return "fiis"
    return "acoes"
