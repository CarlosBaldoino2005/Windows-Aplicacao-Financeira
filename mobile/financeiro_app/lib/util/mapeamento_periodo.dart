/// Mapeamento de periodos da interface para Yahoo Chart e Brapi.
class MapeamentoPeriodo {
  static const String marcaDias = '__dias__';

  static const Map<String, Map<String, dynamic>> yahooChart = {
    'dia': {'range': '1d', 'interval': '5m'},
    'semana': {'range': '5d', 'interval': '30m'},
    'mes': {'range': '1mo', 'interval': '1d'},
    'trimestre': {'range': '3mo', 'interval': '1d'},
    'semestre': {'range': '6mo', 'interval': '1d'},
    'ano': {'range': '1y', 'interval': '1d'},
    'tres_anos': {'range': marcaDias, 'interval': '1d', 'dias': 365 * 3},
    'cinco_anos': {'range': '5y', 'interval': '1d'},
  };

  static const Map<String, Map<String, dynamic>> brapi = {
    'dia': {'range': '1d', 'interval': '1d'},
    'semana': {'range': '5d', 'interval': '1d'},
    'mes': {'range': '1mo', 'interval': '1d'},
    'trimestre': {'range': '3mo', 'interval': '1d'},
    'semestre': {'range': '6mo', 'interval': '1d'},
    'ano': {'range': '1y', 'interval': '1d'},
    'tres_anos': {'range': '5y', 'interval': '1d', 'dias': 365 * 3},
    'cinco_anos': {'range': '5y', 'interval': '1d'},
  };

  static bool usaJanelaEmDias(Map<String, dynamic> cfg) {
    return cfg['range'] == marcaDias;
  }

  static int? diasDoPeriodo(Map<String, dynamic> cfg) {
    final dias = cfg['dias'];
    if (dias is int) return dias;
    if (dias is num) return dias.toInt();
    return null;
  }
}
