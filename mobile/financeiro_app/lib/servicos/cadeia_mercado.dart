import '../modelos/cotacao_resumo.dart';
import '../modelos/serie_historica.dart';
import 'provedores/brapi_provedor.dart';
import 'provedores/yahoo_chart_provedor.dart';

/// Orquestra Brapi e Yahoo Chart com fallback (sem yfinance no mobile).
class CadeiaMercado {
  CadeiaMercado({
    BrapiProvedor? brapi,
    YahooChartProvedor? yahooChart,
  })  : _brapi = brapi ?? BrapiProvedor(),
        _yahooChart = yahooChart ?? YahooChartProvedor();

  final BrapiProvedor _brapi;
  final YahooChartProvedor _yahooChart;

  Future<List<CotacaoResumo>> buscarResumos(List<String> simbolos) async {
    if (simbolos.isEmpty) return [];

    final obtidos = <String, CotacaoResumo>{};
    var pendentes = List<String>.from(simbolos);

    for (final provedor in [_brapi, _yahooChart]) {
      if (pendentes.isEmpty) break;
      List<CotacaoResumo> lote;
      if (provedor is BrapiProvedor) {
        lote = await provedor.buscarResumos(pendentes);
      } else {
        lote = await _yahooChart.buscarResumos(pendentes);
      }
      for (final resumo in lote) {
        obtidos.putIfAbsent(resumo.simbolo, () => resumo);
      }
      pendentes = pendentes.where((s) => !obtidos.containsKey(s)).toList();
    }

    return obtidos.values.toList();
  }

  Future<SerieHistorica?> buscarHistorico(String simbolo, String periodoChave) async {
    for (final provedor in [_brapi, _yahooChart]) {
      final SerieHistorica? serie;
      if (provedor is BrapiProvedor) {
        serie = await provedor.buscarHistorico(simbolo, periodoChave);
      } else {
        serie = await _yahooChart.buscarHistorico(simbolo, periodoChave);
      }
      if (serie != null && serie.pontos.isNotEmpty) return serie;
    }
    return null;
  }
}
