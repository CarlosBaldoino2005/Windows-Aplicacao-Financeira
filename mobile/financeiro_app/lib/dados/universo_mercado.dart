/// Listas de ativos monitorados (espelho de src/Model/*_universo.py).
class IndiceMercado {
  const IndiceMercado({required this.simbolo, required this.nome, required this.regiao});

  final String simbolo;
  final String nome;
  final String regiao;
}

class UniversoMercado {
  static const List<String> acoesB3 = [
    'PETR3', 'PETR4', 'VALE3', 'ITUB4', 'BBDC3', 'BBDC4', 'WEGE3', 'ABEV3', 'MGLU3',
    'BBAS3', 'SANB11', 'B3SA3', 'SUZB3', 'RENT3', 'LREN3', 'RADL3', 'VIVT3', 'TIMS3',
    'CMIG4', 'CSAN3', 'GGBR4', 'USIM5', 'CSNA3', 'EMBR3', 'AZUL4', 'GOLL4', 'HAPV3',
    'KLBN11', 'TAEE11', 'EGIE3', 'CPLE6', 'ENBR3', 'PRIO3', 'RRRP3', 'BPAC11', 'ITSA4',
    'SBSP3', 'TRPL4', 'ELET3', 'ELET6', 'VBBR3', 'RDOR3', 'NTCO3', 'MRFG3', 'BEEF3',
    'TOTS3', 'FLRY3', 'CYRE3', 'YDUQ3', 'CRFB3',
  ];

  static const List<String> acoesEua = [
    'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD', 'INTC', 'NFLX',
    'DIS', 'JPM', 'V', 'MA', 'WMT',
  ];

  static const List<String> criptomoedas = [
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'SOL-USD', 'ADA-USD', 'DOGE-USD',
    'AVAX-USD', 'DOT-USD', 'LINK-USD', 'MATIC-USD', 'POL-USD', 'LTC-USD', 'BCH-USD',
    'ATOM-USD', 'UNI-USD', 'ETC-USD', 'XLM-USD', 'FIL-USD', 'APT-USD', 'ARB-USD',
    'OP-USD', 'NEAR-USD', 'ICP-USD', 'HBAR-USD', 'VET-USD', 'ALGO-USD', 'AAVE-USD',
    'GRT-USD', 'SAND-USD', 'MANA-USD', 'AXS-USD', 'EGLD-USD', 'XTZ-USD', 'THETA-USD',
    'EOS-USD',
  ];

  static const Map<String, String> nomesCripto = {
    'BTC-USD': 'Bitcoin',
    'ETH-USD': 'Ethereum',
    'BNB-USD': 'BNB',
    'XRP-USD': 'Ripple',
    'SOL-USD': 'Solana',
    'ADA-USD': 'Cardano',
    'DOGE-USD': 'Dogecoin',
    'AVAX-USD': 'Avalanche',
    'DOT-USD': 'Polkadot',
    'LINK-USD': 'Chainlink',
    'MATIC-USD': 'Polygon (MATIC)',
    'POL-USD': 'Polygon (POL)',
    'LTC-USD': 'Litecoin',
    'BCH-USD': 'Bitcoin Cash',
    'ATOM-USD': 'Cosmos',
    'UNI-USD': 'Uniswap',
  };

  static const Set<String> unidadesNaoFii = {
    'TAEE11', 'SANB11', 'SAPR11', 'KLBN11', 'BPAC11',
  };

  static const List<String> fiisB3 = [
    'HGLG11', 'XPLG11', 'MXRF11', 'KNCR11', 'KNRI11', 'HGRU11', 'BCFF11', 'RBRR11',
    'VISC11', 'LVBI11', 'HFOF11', 'XPML11', 'BTLG11', 'RECR11', 'VILG11', 'PVBI11',
    'GARE11', 'IRIM11', 'CPTS11', 'HSML11', 'JSRE11', 'GGRC11', 'VRTA11', 'MCCI11',
    'RZAK11', 'TGAR11', 'TRXF11', 'KNSC11', 'BRCO11', 'XPCI11', 'HABT11', 'VCJR11',
    'MGFF11', 'RBVA11', 'MALL11', 'DEVA11', 'JSAF11', 'ALZR11', 'BRCR11', 'HSLG11',
    'KNHF11', 'VGHF11', 'HGRE11', 'RBRF11', 'PLCR11', 'SNCI11', 'BTCI11', 'MFII11',
    'QAGR11', 'CVBI11', 'RZTR11',
  ];

  static const List<IndiceMercado> indices = [
    IndiceMercado(simbolo: '^BVSP', nome: 'Ibovespa', regiao: 'Brasil'),
    IndiceMercado(simbolo: '^IFIX', nome: 'IFIX (Fundos Imobiliarios)', regiao: 'Brasil'),
    IndiceMercado(simbolo: 'BOVA11.SA', nome: 'ETF Ibovespa (BOVA11)', regiao: 'Brasil'),
    IndiceMercado(simbolo: 'SMAL11.SA', nome: 'ETF Small Caps (SMAL11)', regiao: 'Brasil'),
    IndiceMercado(simbolo: '^GSPC', nome: 'S&P 500', regiao: 'EUA'),
    IndiceMercado(simbolo: '^IXIC', nome: 'Nasdaq Composite', regiao: 'EUA'),
    IndiceMercado(simbolo: '^DJI', nome: 'Dow Jones', regiao: 'EUA'),
    IndiceMercado(simbolo: 'SPY', nome: 'ETF S&P 500 (SPY)', regiao: 'EUA'),
    IndiceMercado(simbolo: 'QQQ', nome: 'ETF Nasdaq (QQQ)', regiao: 'EUA'),
    IndiceMercado(simbolo: '^STOXX50E', nome: 'Euro Stoxx 50', regiao: 'Europa'),
    IndiceMercado(simbolo: '^FTSE', nome: 'FTSE 100', regiao: 'Europa'),
    IndiceMercado(simbolo: '^N225', nome: 'Nikkei 225', regiao: 'Asia'),
    IndiceMercado(simbolo: '^HSI', nome: 'Hang Seng', regiao: 'Asia'),
    IndiceMercado(simbolo: 'EWZ', nome: 'ETF Brasil (EWZ)', regiao: 'Global'),
    IndiceMercado(simbolo: 'DIA', nome: 'ETF Dow Jones (DIA)', regiao: 'EUA'),
  ];

  static List<String> montarAcoesMonitoradas(int limite) {
    final resultado = <String>[];
    final vistos = <String>{};
    for (final codigo in acoesB3) {
      final simbolo = codigo.endsWith('.SA') ? codigo : '$codigo.SA';
      if (vistos.add(simbolo)) resultado.add(simbolo);
      if (resultado.length >= limite) return resultado;
    }
    for (final codigo in acoesEua) {
      if (vistos.add(codigo)) resultado.add(codigo);
      if (resultado.length >= limite) break;
    }
    return resultado;
  }

  static List<String> montarCriptoMonitoradas(int limite) {
    final max = limite.clamp(1, criptomoedas.length);
    return criptomoedas.take(max).toList();
  }

  static List<String> montarFiisMonitorados(int limite) {
    final resultado = <String>[];
    final vistos = <String>{};
    for (final codigo in fiisB3) {
      final simbolo = codigo.endsWith('.SA') ? codigo : '$codigo.SA';
      if (vistos.add(simbolo)) resultado.add(simbolo);
      if (resultado.length >= limite) return resultado;
    }
    return resultado;
  }

  static List<String> montarIndices(int limite) {
    final max = limite.clamp(1, indices.length);
    return indices.take(max).map((i) => i.simbolo).toList();
  }
}
