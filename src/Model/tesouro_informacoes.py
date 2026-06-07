"""Textos educativos sobre titulos do Tesouro Direto (por familia e geral)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndicadorTesouro:
    """Indicador exibido na tela de detalhes."""

    rotulo: str
    valor: str
    explicacao: str


@dataclass(frozen=True)
class InformacoesFamiliaTesouro:
    """Metadados educativos de uma familia de titulos."""

    nome: str
    resumo: str
    rentabilidade: str
    volatilidade: str
    liquidez: str
    risco: str
    perfil_investidor: str
    tributacao: str
    pagamento_juros: str
    investimento_minimo: str
    quando_faz_sentido: str


MAPA_TIPO_PARA_FAMILIA: dict[str, str] = {
    "Tesouro Selic": "Selic",
    "Tesouro Prefixado": "Prefixado",
    "Tesouro Prefixado com Juros Semestrais": "Prefixado com juros",
    "Tesouro IPCA+": "IPCA+",
    "Tesouro IPCA+ com Juros Semestrais": "IPCA+ com juros",
    "Tesouro IGPM+ com Juros Semestrais": "IGPM+ com juros",
    "Tesouro Educa+": "Educa+",
    "Tesouro Renda+ Aposentadoria Extra": "Renda+",
}


INFORMACOES_FAMILIAS: dict[str, InformacoesFamiliaTesouro] = {
    "Selic": InformacoesFamiliaTesouro(
        nome="Tesouro Selic (LFT)",
        resumo=(
            "Titulo pos-fixado atrelado a taxa Selic. Acompanha de perto a politica "
            "monetaria e e referencia de liquidez e baixa volatilidade entre os titulos publicos."
        ),
        rentabilidade="Pos-fixada: rende conforme a taxa Selic (com pequeno spread de mercado).",
        volatilidade="Baixa no curto prazo quando mantido ate o vencimento; oscila pouco em relacao a prefixados e IPCA+.",
        liquidez="Alta no Tesouro Direto: recompra diaria pelo Tesouro Nacional, em geral com liquidacao em D+1.",
        risco="Credito soberano (Uniao). Risco de mercado baixo se carregado ate o vencimento.",
        perfil_investidor="Reserva de emergencia, objetivos de curto prazo e quem busca previsibilidade pos-fixada.",
        tributacao="IR regressivo (22,5% a 15%) sobre o rendimento; IOF se resgatar antes de 30 dias.",
        pagamento_juros="Sem cupons semestrais: juros incorporados ao valor do titulo.",
        investimento_minimo="A partir de cerca de R$ 30 (fracao minima definida pelo Tesouro).",
        quando_faz_sentido="Quando a Selic esta elevada ou voce precisa de liquidez com baixa oscilacao de preco.",
    ),
    "Prefixado": InformacoesFamiliaTesouro(
        nome="Tesouro Prefixado (LTN)",
        resumo=(
            "Titulo com taxa fixa definida na compra. Voce sabe qual rendimento recebera "
            "se mantiver o titulo ate o vencimento."
        ),
        rentabilidade="Prefixada: taxa contratada na compra (ex.: 12,50% ao ano).",
        volatilidade=(
            "Moderada a alta no preco (PU) antes do vencimento: sobe quando juros caem "
            "e cai quando juros sobem. Mantido ate o vencimento, o rendimento e o contratado."
        ),
        liquidez="Alta no Tesouro Direto (recompra diaria, liquidacao tipica D+1).",
        risco="Credito soberano. Risco de mercado (marca a mercado) se vender antes do vencimento.",
        perfil_investidor="Quem acredita que juros vao cair ou tem horizonte ate o vencimento definido.",
        tributacao="IR regressivo sobre rendimento; IOF abaixo de 30 dias.",
        pagamento_juros="Sem cupons: ganho via valorizacao do titulo ate o vencimento.",
        investimento_minimo="A partir de cerca de R$ 30.",
        quando_faz_sentido="Travar taxa alta em cenarios de queda esperada de juros ou meta com data certa.",
    ),
    "Prefixado com juros": InformacoesFamiliaTesouro(
        nome="Tesouro Prefixado com Juros Semestrais (NTN-F)",
        resumo=(
            "Titulo prefixado que paga cupons de juros a cada seis meses, alem da "
            "valorizacao ou amortizacao no vencimento."
        ),
        rentabilidade="Prefixada com cupons semestrais; taxa definida na compra.",
        volatilidade="Moderada a alta no PU; cupons reduzem a necessidade de vender o titulo inteiro para renda.",
        liquidez="Alta no Tesouro Direto.",
        risco="Credito soberano; risco de mercado se vender antes do vencimento.",
        perfil_investidor="Quem quer renda periodica prefixada (aposentadoria, complemento de renda).",
        tributacao="IR sobre cupons e sobre ganho na venda; IOF abaixo de 30 dias.",
        pagamento_juros="Cupons semestrais creditados na conta.",
        investimento_minimo="A partir de cerca de R$ 30.",
        quando_faz_sentido="Gerar fluxo de caixa previsivel com taxa fixa conhecida.",
    ),
    "IPCA+": InformacoesFamiliaTesouro(
        nome="Tesouro IPCA+ (NTN-B Principal)",
        resumo=(
            "Titulo que paga inflacao (IPCA) mais uma taxa real fixa. Protege o poder "
            "de compra e e referencia para metas de longo prazo."
        ),
        rentabilidade="IPCA + taxa real fixa (ex.: IPCA + 6,00% ao ano).",
        volatilidade=(
            "Alta no PU antes do vencimento por causa de juros reais e expectativa de inflacao. "
            "Carregado ate o vencimento, entrega IPCA + taxa contratada."
        ),
        liquidez="Alta no Tesouro Direto.",
        risco="Credito soberano; risco de mercado na marcacao a mercado antes do vencimento.",
        perfil_investidor="Longo prazo, aposentadoria, protecao contra inflacao.",
        tributacao="IR regressivo; IOF abaixo de 30 dias.",
        pagamento_juros="Sem cupons: juros e correcao incorporados ao titulo.",
        investimento_minimo="A partir de cerca de R$ 30.",
        quando_faz_sentido="Metas acima de 5 anos com necessidade de superar a inflacao.",
    ),
    "IPCA+ com juros": InformacoesFamiliaTesouro(
        nome="Tesouro IPCA+ com Juros Semestrais (NTN-B)",
        resumo=(
            "Combina protecao contra inflacao (IPCA) com taxa real fixa e pagamento "
            "de cupons semestrais."
        ),
        rentabilidade="IPCA + taxa real, com cupons semestrais.",
        volatilidade="Alta no PU; cupons ajudam a monetizar parte do retorno sem vender o titulo.",
        liquidez="Alta no Tesouro Direto.",
        risco="Credito soberano; oscilacao de preco se vender antes do vencimento.",
        perfil_investidor="Renda real periodica com protecao inflacionaria.",
        tributacao="IR sobre cupons e ganho de capital; IOF abaixo de 30 dias.",
        pagamento_juros="Cupons semestrais (parte inflacao + parte taxa real).",
        investimento_minimo="A partir de cerca de R$ 30.",
        quando_faz_sentido="Complemento de renda indexado a inflacao.",
    ),
    "IGPM+ com juros": InformacoesFamiliaTesouro(
        nome="Tesouro IGPM+ com Juros Semestrais",
        resumo=(
            "Titulo indexado ao IGPM (indice usado em contratos de aluguel) com taxa "
            "fixa adicional e cupons semestrais."
        ),
        rentabilidade="IGPM + taxa fixa, com cupons semestrais.",
        volatilidade="Alta no PU; IGPM pode divergir do IPCA em alguns periodos.",
        liquidez="Alta no Tesouro Direto quando o titulo esta em oferta.",
        risco="Credito soberano; risco de indice (IGPM vs inflacao oficial) e de mercado.",
        perfil_investidor="Quem deseja exposicao ao IGPM com renda semestral.",
        tributacao="IR regressivo; IOF abaixo de 30 dias.",
        pagamento_juros="Cupons semestrais.",
        investimento_minimo="A partir de cerca de R$ 30.",
        quando_faz_sentido="Diversificacao de indexador ou expectativa especifica sobre IGPM.",
    ),
    "Educa+": InformacoesFamiliaTesouro(
        nome="Tesouro Educa+",
        resumo=(
            "Titulo de longo prazo voltado a custear educacao. Combina caracteristicas "
            "de prefixado ou IPCA+ conforme a serie, com foco em planejamento familiar."
        ),
        rentabilidade="Varia conforme a serie (prefixada ou atrelada a inflacao).",
        volatilidade="Moderada a alta no PU antes do vencimento.",
        liquidez="Alta no Tesouro Direto enquanto ofertado.",
        risco="Credito soberano; planejamento de longo prazo.",
        perfil_investidor="Pais ou responsaveis que poupam para faculdade ou estudos.",
        tributacao="IR regressivo; IOF abaixo de 30 dias.",
        pagamento_juros="Conforme modalidade da serie (ver vencimento e tipo).",
        investimento_minimo="A partir de cerca de R$ 30.",
        quando_faz_sentido="Objetivo educacional com horizonte de varios anos.",
    ),
    "Renda+": InformacoesFamiliaTesouro(
        nome="Tesouro Renda+ Aposentadoria Extra",
        resumo=(
            "Titulo pensado para complemento de aposentadoria, com fluxo na fase de usufruto "
            "e acumulacao na fase de contribuicao."
        ),
        rentabilidade="Atrelado a inflacao (IPCA) com regras especificas do programa Renda+.",
        volatilidade="Moderada a alta no PU durante a fase de acumulacao.",
        liquidez="Alta no Tesouro Direto durante a oferta; atencao as regras de resgate/usufruto.",
        risco="Credito soberano; entender fases de acumulacao e renda antes de investir.",
        perfil_investidor="Planejamento previdenciario complementar de longo prazo.",
        tributacao="IR conforme regras do titulo e momento de resgate/usufruto.",
        pagamento_juros="Fluxo programado na fase de usufruto (apos periodo de acumulacao).",
        investimento_minimo="A partir de cerca de R$ 30.",
        quando_faz_sentido="Construir renda futura indexada a inflacao para aposentadoria.",
    ),
}


def obter_familia_por_tipo(tipo_titulo: str) -> str:
    """Mapeia o nome completo do CSV para a familia usada na interface."""
    return MAPA_TIPO_PARA_FAMILIA.get(tipo_titulo.strip(), "Outros")


def obter_informacoes_familia(familia: str) -> InformacoesFamiliaTesouro | None:
    """Retorna metadados educativos da familia, se existir."""
    return INFORMACOES_FAMILIAS.get(familia)


def obter_indicadores_gerais_tesouro() -> list[IndicadorTesouro]:
    """Indicadores gerais do programa Tesouro Direto."""
    return [
        IndicadorTesouro(
            "Emissor",
            "Uniao (Tesouro Nacional)",
            "Titulos publicos federais considerados referencia de baixo risco de credito no Brasil.",
        ),
        IndicadorTesouro(
            "Plataforma",
            "Tesouro Direto",
            "Negociacao via corretoras habilitadas; precos e taxas publicados diariamente.",
        ),
        IndicadorTesouro(
            "Horario",
            "Ate ~18h (dias uteis)",
            "Cotacoes e operacoes seguem calendario da B3/Tesouro; fora do horario usa ultima cotacao.",
        ),
        IndicadorTesouro(
            "Liquidez",
            "Alta (recompra diaria)",
            "O Tesouro recompra titulos diariamente; valor creditado em geral em D+1 util.",
        ),
        IndicadorTesouro(
            "Investimento minimo",
            "~ R$ 30",
            "Fracao minima por titulo definida pelo programa; pode variar conforme PU.",
        ),
        IndicadorTesouro(
            "Taxa da corretora",
            "0,20% ao ano (max.)",
            "Taxa de custodia Tesouro Direto cobrada semestralmente sobre saldo; corretora pode zerar.",
        ),
        IndicadorTesouro(
            "Imposto de Renda",
            "Tabela regressiva",
            "22,5% (ate 180 dias), 20%, 17,5% e 15% (acima de 720 dias) sobre o rendimento.",
        ),
        IndicadorTesouro(
            "IOF",
            "Regressivo ate 30 dias",
            "Incide sobre rendimento se resgatar antes de 30 dias da aplicacao.",
        ),
        IndicadorTesouro(
            "FGC",
            "Nao se aplica",
            "Titulos publicos nao sao cobertos pelo FGC; risco de credito e da Uniao.",
        ),
    ]


def montar_identificador_titulo(tipo_titulo: str, data_vencimento_texto: str) -> str:
    """Chave unica estavel para listagem e detalhes."""
    return f"{tipo_titulo}|{data_vencimento_texto}"
