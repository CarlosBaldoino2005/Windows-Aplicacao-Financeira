"""Textos didaticos dos indicadores exibidos na aba Mais detalhes."""

from __future__ import annotations

# Chave = rotulo exibido na tela; valor = explicacao para usuario leigo.
EXPLICACOES_INDICADORES: dict[str, str] = {
    "Preco atual": (
        "Valor de uma acao ou cota neste momento (ou no ultimo pregão). "
        "E o preco que voce veria ao comprar ou vender agora no mercado."
    ),
    "Capitalizacao": (
        "Soma do valor de todas as acoes da empresa no mercado. "
        "Mostra o tamanho da companhia: quanto o mercado avalia a empresa como um todo."
    ),
    "Capitalizacao de mercado": (
        "Valor total de todas as moedas em circulacao, multiplicado pelo preco atual. "
        "Indica o tamanho e a importancia da criptomoeda no mercado."
    ),
    "Receita (TTM)": (
        "Dinheiro que a empresa faturou nos ultimos 12 meses (TTM = ultimos doze meses). "
        "Mostra quanto a empresa vendeu, antes de descontar custos e impostos."
    ),
    "Lucro liquido (TTM)": (
        "Quanto a empresa lucrou de verdade nos ultimos 12 meses, depois de pagar "
        "custos, despesas e impostos. Lucro positivo indica que sobrou dinheiro no periodo."
    ),
    "EBITDA": (
        "Lucro operacional aproximado, antes de juros, impostos, depreciacao e amortizacao. "
        "Ajuda a comparar o desempenho do negocio principal, sem efeitos contabeis extras."
    ),
    "Margem de lucro": (
        "Porcentagem do faturamento que virou lucro. "
        "Exemplo: 10% significa que, a cada R$ 100 vendidos, R$ 10 ficaram de lucro."
    ),
    "Margem operacional": (
        "Porcentagem da receita que sobrou das operacoes do dia a dia da empresa. "
        "Mostra se o negocio principal e eficiente, antes de juros e impostos."
    ),
    "ROE": (
        "Retorno sobre o patrimonio (Return on Equity). "
        "Mede quanto lucro a empresa gera com o dinheiro dos acionistas. "
        "Quanto maior, melhor costuma ser o aproveitamento do capital proprio."
    ),
    "P/L (trailing)": (
        "Preco dividido pelo lucro dos ultimos 12 meses. "
        "Indica quantos anos de lucro atual o mercado esta pagando no preco da acao. "
        "Numero alto pode significar expectativa de crescimento; numero baixo, acao mais barata."
    ),
    "P/L (forward)": (
        "Preco dividido pelo lucro esperado para os proximos 12 meses. "
        "Usa estimativas de analistas sobre o futuro da empresa."
    ),
    "P/L": (
        "Preco da acao dividido pelo lucro por acao. "
        "Ajuda a comparar se a acao esta cara ou barata em relacao ao lucro que gera."
    ),
    "Lucro por acao": (
        "Lucro da empresa dividido pelo numero de acoes. "
        "Mostra quanto de lucro cada acao 'representa' no periodo."
    ),
    "Dividend yield": (
        "Rendimento dos dividendos em relacao ao preco da acao (em %). "
        "Indica quanto a empresa pagou em proventos nos ultimos 12 meses, "
        "comparado ao preco atual — util para quem busca renda."
    ),
    "Ultimo dividendo pago": (
        "Valor e data do pagamento de proventos mais recente. "
        "Dividendos sao parte do lucro distribuida aos acionistas."
    ),
    "Beta": (
        "Mede o quanto a acao costuma subir ou cair junto com o mercado. "
        "Beta perto de 1 acompanha o indice; acima de 1 oscila mais; abaixo de 1, oscila menos."
    ),
    "Divida/Patrimonio": (
        "Quanto a empresa deve em relacao ao que os acionistas investiram. "
        "Numero alto pode indicar mais endividamento e, portanto, mais risco financeiro."
    ),
    "Liquidez corrente": (
        "Capacidade de pagar contas de curto prazo com o que a empresa tem disponivel. "
        "Acima de 1, em geral, sugere que ha recursos suficientes para honrar obrigacoes proximas."
    ),
    "Max. 52 semanas": (
        "Maior preco atingido nos ultimos 12 meses. "
        "Serve de referencia para ver se o ativo esta perto da maxima recente."
    ),
    "Min. 52 semanas": (
        "Menor preco atingido nos ultimos 12 meses. "
        "Ajuda a enxergar a distancia entre o preco atual e o ponto mais baixo do ano."
    ),
    "Recomendacao analistas": (
        "Resumo da opiniao media dos analistas sobre a acao "
        "(por exemplo: comprar, manter ou vender). "
        "E uma referencia de mercado, nao uma garantia de resultado."
    ),
    "Opinioes de analistas": (
        "Quantidade de analistas que emitiram recomendacao sobre a acao. "
        "Mais opinioes costumam dar mais confianca estatistica a media do mercado."
    ),
    "Setor": (
        "Grande area de atuacao da empresa (ex.: financeiro, energia, tecnologia). "
        "Ajuda a comparar a companhia com outras do mesmo tipo de negocio."
    ),
    "Industria": (
        "Ramo mais especifico dentro do setor (ex.: bancos, petroleo, varejo). "
        "Permite comparacoes mais detalhadas entre empresas parecidas."
    ),
    "Funcionarios": (
        "Numero estimado de colaboradores da empresa. "
        "Da uma ideia do porte operacional da companhia."
    ),
    "Variacao do dia": (
        "Quanto o preco subiu ou caiu hoje, em porcentagem, em relacao ao fechamento anterior. "
        "Mostra o movimento mais recente do ativo."
    ),
    "Faixa de preco (dia/52s)": (
        "Menor e maior preco negociado no dia ou nos ultimos 12 meses. "
        "Mostra a amplitude de oscilacao recente do ativo."
    ),
    "Volume 24h": (
        "Quantidade negociada nas ultimas 24 horas. "
        "Volume alto costuma indicar mais interesse e liquidez no mercado."
    ),
    "Volume (todas moedas)": (
        "Volume total negociado considerando todas as plataformas e pares de moedas. "
        "Da uma visao mais ampla da movimentacao da criptomoeda."
    ),
    "Oferta em circulacao": (
        "Quantidade de moedas que ja existem e podem ser negociadas hoje. "
        "Quanto maior a oferta, mais moedas ha disponiveis no mercado."
    ),
    "Oferta maxima": (
        "Limite maximo de moedas que podem existir, quando definido pelo projeto. "
        "Algumas criptos tem quantidade limitada (como o Bitcoin); outras nao tem teto fixo."
    ),
    "Maximo historico": (
        "Maior preco ja registrado desde o lancamento da moeda. "
        "Referencia para comparar o preco atual com o pico de todos os tempos."
    ),
    "Minimo historico": (
        "Menor preco ja registrado desde o lancamento. "
        "Mostra o fundo historico e ajuda a medir a recuperacao do ativo."
    ),
    "Media volume (10 dias)": (
        "Media de negociacoes dos ultimos 10 dias. "
        "Compara o interesse recente com o volume de hoje."
    ),
    "Media volume": (
        "Media de negociacoes em um periodo mais longo. "
        "Ajuda a ver se o volume atual esta acima ou abaixo do habitual."
    ),
    "Variacao 52 semanas": (
        "Quanto o preco subiu ou caiu nos ultimos 12 meses, em porcentagem. "
        "Resume o desempenho do ativo no ultimo ano."
    ),
    "Preco de abertura": (
        "Primeiro preco negociado no dia (ou no ultimo pregão). "
        "Ponto de partida para calcular a variacao do dia."
    ),
    "Preco anterior": (
        "Preco de fechamento do pregão anterior. "
        "Base usada para medir se o ativo subiu ou caiu hoje."
    ),
    "Algoritmo": (
        "Tecnologia ou regra de consenso usada pela rede da criptomoeda "
        "(por exemplo, prova de trabalho ou prova de participacao)."
    ),
    "Moeda base": (
        "Codigo da moeda digital representada (ex.: BTC, ETH). "
        "Identifica qual ativo esta sendo cotado."
    ),
    "Data de lancamento": (
        "Data em que a criptomoeda foi criada ou passou a ser negociada. "
        "Indica a idade e a maturidade do projeto no mercado."
    ),
}

_EXPLICACAO_PADRAO = (
    "Indicador financeiro relacionado ao desempenho, tamanho ou perfil deste ativo. "
    "Passe o mouse sobre outros indicadores para ver explicacoes detalhadas."
)


def obter_explicacao_indicador(rotulo: str) -> str:
    """Retorna texto didatico para o rotulo do indicador."""
    if not rotulo or not str(rotulo).strip():
        return _EXPLICACAO_PADRAO
    chave = str(rotulo).strip()
    return EXPLICACOES_INDICADORES.get(chave, _EXPLICACAO_PADRAO)
