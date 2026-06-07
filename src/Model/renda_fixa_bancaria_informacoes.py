"""Informacoes educativas sobre LCI, LCA e CDB."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndicadorRendaFixa:
    rotulo: str
    valor: str
    explicacao: str


@dataclass(frozen=True)
class InformacoesProdutoRendaFixa:
    nome: str
    sigla: str
    resumo: str
    emissor: str
    rentabilidade: str
    liquidez: str
    risco: str
    tributacao: str
    fgc: str
    investimento_minimo: str
    indexadores: str
    quando_faz_sentido: str
    cuidados: str


INFORMACOES_LCI = InformacoesProdutoRendaFixa(
    nome="Letra de Credito Imobiliario",
    sigla="LCI",
    resumo=(
        "Titulo de renda fixa emitido por banco para captar recursos destinados ao "
        "setor imobiliario. Para pessoa fisica, o rendimento e isento de Imposto de Renda."
    ),
    emissor="Bancos e instituicoes financeiras autorizadas pelo Banco Central.",
    rentabilidade=(
        "Em geral atrelada ao CDI (ex.: 90%, 95%, 100% CDI) ou taxa prefixada. "
        "A taxa e definida no momento da aplicacao e consta no certificado."
    ),
    liquidez=(
        "Baixa liquidez antes do vencimento na maioria das ofertas. "
        "Pode haver mercado secundario limitado; resgate antecipado depende das regras do banco."
    ),
    risco="Credito do emissor (banco). Cobertura do FGC ate o limite legal por CPF e instituicao.",
    tributacao="Isenta de IR para pessoa fisica. IOF se resgatar antes de 30 dias.",
    fgc="Coberta pelo FGC ate R$ 250 mil por CPF por instituicao (principal + rendimentos).",
    investimento_minimo="Varia por banco; comum a partir de R$ 1.000 ou R$ 5.000.",
    indexadores="CDI (pos-fixado) ou taxa prefixada anual.",
    quando_faz_sentido=(
        "Metas de medio prazo com foco em isencao de IR, comparando sempre a taxa liquida "
        "equivalente de um CDB ou Tesouro tributado."
    ),
    cuidados=(
        "Confirme carencia, vencimento, possibilidade de resgate antecipado e se a taxa "
        "e bruta (% CDI) ou equivalente. Compare com CDB do mesmo prazo descontando o IR."
    ),
)

INFORMACOES_LCA = InformacoesProdutoRendaFixa(
    nome="Letra de Credito do Agronegocio",
    sigla="LCA",
    resumo=(
        "Titulo de renda fixa emitido por banco para financiar o agronegocio. "
        "Para pessoa fisica, tambem e isento de Imposto de Renda sobre o rendimento."
    ),
    emissor="Bancos e instituicoes financeiras autorizadas pelo Banco Central.",
    rentabilidade=(
        "Semelhante a LCI: costuma pagar percentual do CDI ou taxa prefixada, "
        "conforme a oferta do banco no momento da aplicacao."
    ),
    liquidez=(
        "Em geral sem liquidez diaria; prazo minimo (carencia) e vencimento fixos. "
        "Resgate antecipado segue regras especificas de cada emissor."
    ),
    risco="Credito do emissor. Protecao do FGC dentro dos limites legais.",
    tributacao="Isenta de IR para pessoa fisica. IOF em resgates antes de 30 dias.",
    fgc="Coberta pelo FGC ate R$ 250 mil por CPF por instituicao.",
    investimento_minimo="Varia por banco; frequentemente a partir de R$ 1.000.",
    indexadores="CDI ou taxa prefixada.",
    quando_faz_sentido=(
        "Quando a taxa ofertada supera alternativas tributadas (CDB) apos considerar a isencao de IR."
    ),
    cuidados=(
        "LCI e LCA tem finalidade setorial para o banco; para o investidor o comparativo "
        "pratico e taxa, prazo, liquidez e risco de credito — nao o setor financiado."
    ),
)

INFORMACOES_CDB = InformacoesProdutoRendaFixa(
    nome="Certificado de Deposito Bancario",
    sigla="CDB",
    resumo=(
        "Titulo de renda fixa emitido por banco. E o produto bancario mais comum para "
        "pessoa fisica, com rendimento sujeito a Imposto de Renda regressivo."
    ),
    emissor="Bancos comercial, multiplo, de investimento e fintechs autorizadas.",
    rentabilidade=(
        "Pode ser pos-fixado (% do CDI, ex.: 100% ou 110% CDI) ou prefixado (taxa fixa aa). "
        "CDBs indexados ao IPCA tambem existem em alguns bancos."
    ),
    liquidez=(
        "Depende da oferta: ha CDBs com liquidez diaria e outros com carencia ate o vencimento. "
        "Verifique no certificado ou app do banco."
    ),
    risco="Credito do emissor. Cobertura FGC ate o limite por CPF e instituicao.",
    tributacao="IR regressivo sobre o rendimento (22,5% a 15%). IOF se resgatar antes de 30 dias.",
    fgc="Coberto pelo FGC ate R$ 250 mil por CPF por instituicao.",
    investimento_minimo="Desde R$ 1 em alguns bancos digitais; tradicionais costumam exigir mais.",
    indexadores="CDI, prefixado ou IPCA+ (conforme emissor).",
    quando_faz_sentido=(
        "Reserva de emergencia (liquidez diaria), metas de curto/medio prazo ou quando a taxa "
        "liquida supera LCI/LCA disponiveis no mesmo prazo."
    ),
    cuidados=(
        "Compare sempre o rendimento liquido apos IR. Um CDB de 100% CDI pode perder para "
        "LCI/LCA de 90% CDI por causa da isencao. Atencao a carencia e resgate antecipado."
    ),
)


def obter_informacoes_lci() -> InformacoesProdutoRendaFixa:
    return INFORMACOES_LCI


def obter_informacoes_lca() -> InformacoesProdutoRendaFixa:
    return INFORMACOES_LCA


def obter_informacoes_cdb() -> InformacoesProdutoRendaFixa:
    return INFORMACOES_CDB


def obter_indicadores_gerais_renda_fixa() -> list[IndicadorRendaFixa]:
    return [
        IndicadorRendaFixa(
            "FGC",
            "Ate R$ 250 mil / CPF / instituicao",
            "Fundo Garantidor de Creditos cobre principal e rendimentos se o banco falir, "
            "dentro do limite. Investimentos acima do teto ficam expostos ao risco de credito.",
        ),
        IndicadorRendaFixa(
            "CDI",
            "Referencia pos-fixada",
            "Certificado de Deposito Interbancario; acompanha de perto a Selic. "
            "A maioria dos CDBs/LCIs/LCAs pos-fixados usa % do CDI como remuneracao.",
        ),
        IndicadorRendaFixa(
            "IR — CDB",
            "Regressivo (22,5% a 15%)",
            "Incide sobre o rendimento no resgate. LCI e LCA sao isentas para pessoa fisica.",
        ),
        IndicadorRendaFixa(
            "IOF",
            "Ate 30 dias",
            "Resgate antes de 30 dias da aplicacao pode ter IOF regressivo sobre o rendimento.",
        ),
        IndicadorRendaFixa(
            "Ofertas",
            "Via Meelion (aba Ofertas)",
            "Ranking parcial por distribuidor (app/corretora). Nao substitui o catalogo "
            "completo do banco; confirme taxas antes de aplicar.",
        ),
    ]
