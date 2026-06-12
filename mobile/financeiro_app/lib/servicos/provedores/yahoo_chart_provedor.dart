import 'package:intl/intl.dart';

import '../../modelos/cotacao_resumo.dart';
import '../../modelos/serie_historica.dart';
import '../../util/mapeamento_periodo.dart';
import 'requisicao_provedor.dart';

/// Consulta query1.finance.yahoo.com (mesmo fallback do desktop).
class YahooChartProvedor {
  YahooChartProvedor({RequisicaoProvedor? requisicao})
      : _requisicao = requisicao ?? RequisicaoProvedor();

  final RequisicaoProvedor _requisicao;
  static const String urlChart = 'https://query1.finance.yahoo.com/v8/finance/chart';

  Future<List<CotacaoResumo>> buscarResumos(List<String> simbolos) async {
    final resultados = <CotacaoResumo>[];
    for (final simbolo in simbolos) {
      final resumo = await _resumoPorChart(simbolo, rangeParam: '5d', interval: '1d');
      if (resumo != null) resultados.add(resumo);
    }
    return resultados;
  }

  Future<SerieHistorica?> buscarHistorico(String simbolo, String periodoChave) async {
    final cfg = MapeamentoPeriodo.yahooChart[periodoChave] ??
        MapeamentoPeriodo.yahooChart['mes']!;
    final simboloCodificado = Uri.encodeComponent(simbolo);
    String url;

    if (MapeamentoPeriodo.usaJanelaEmDias(cfg)) {
      final dias = MapeamentoPeriodo.diasDoPeriodo(cfg) ?? 365 * 3;
      final fim = DateTime.now();
      final inicio = fim.subtract(Duration(days: dias));
      final period1 = inicio.millisecondsSinceEpoch ~/ 1000;
      final period2 = (fim.add(const Duration(days: 1))).millisecondsSinceEpoch ~/ 1000;
      url = '$urlChart/$simboloCodificado?period1=$period1&period2=$period2&interval=${cfg['interval']}';
    } else {
      url = '$urlChart/$simboloCodificado?range=${cfg['range']}&interval=${cfg['interval']}';
    }

    final dados = await _requisicao.getJson(url);
    return _serieDeChart(simbolo, periodoChave, dados);
  }

  Future<Map<String, dynamic>?> buscarMeta(String simbolo) async {
    final simboloCodificado = Uri.encodeComponent(simbolo);
    final dados = await _requisicao.getJson('$urlChart/$simboloCodificado?range=5d&interval=1d');
    if (dados == null) return null;
    try {
      final resultados = dados['chart']?['result'] as List<dynamic>?;
      if (resultados == null || resultados.isEmpty) return null;
      final meta = resultados.first['meta'];
      return meta is Map<String, dynamic> ? meta : null;
    } catch (_) {
      return null;
    }
  }

  Future<CotacaoResumo?> _resumoPorChart(
    String simbolo, {
    required String rangeParam,
    required String interval,
  }) async {
    final simboloCodificado = Uri.encodeComponent(simbolo);
    final dados = await _requisicao.getJson(
      '$urlChart/$simboloCodificado?range=$rangeParam&interval=$interval',
    );
    if (dados == null) return null;

    try {
      final meta = dados['chart']['result'][0]['meta'] as Map<String, dynamic>;
      final preco = (meta['regularMarketPrice'] as num).toDouble();
      final anterior = (meta['chartPreviousClose'] ?? meta['previousClose'] ?? preco) as num;
      final variacao = preco - anterior.toDouble();
      final base = anterior.toDouble() != 0 ? anterior.toDouble() : 1.0;
      final moeda = meta['currency']?.toString() ?? (simbolo.endsWith('.SA') ? 'BRL' : 'USD');
      final nome = meta['longName']?.toString() ??
          meta['shortName']?.toString() ??
          simbolo.replaceAll('.SA', '');
      return CotacaoResumo(
        simbolo: simbolo,
        codigo: simbolo.replaceAll('.SA', ''),
        nome: nome,
        preco: double.parse(preco.toStringAsFixed(2)),
        variacaoPercentual: double.parse(((variacao / base) * 100).toStringAsFixed(2)),
        variacaoValor: double.parse(variacao.toStringAsFixed(2)),
        moeda: moeda,
      );
    } catch (_) {
      return null;
    }
  }

  SerieHistorica? _serieDeChart(String simbolo, String rotulo, Map<String, dynamic>? dados) {
    if (dados == null) return null;
    try {
      final resultado = dados['chart']['result'][0] as Map<String, dynamic>;
      final timestamps = (resultado['timestamp'] as List<dynamic>?) ?? [];
      final indicadores = resultado['indicators']['quote'][0] as Map<String, dynamic>;
      final aberturas = (indicadores['open'] as List<dynamic>?) ?? [];
      final fechamentos = (indicadores['close'] as List<dynamic>?) ?? [];
      final volumes = (indicadores['volume'] as List<dynamic>?) ?? [];

      final pontos = <PontoHistorico>[];
      for (var i = 0; i < timestamps.length; i++) {
        final ts = timestamps[i];
        if (ts == null) continue;
        final close = i < fechamentos.length ? fechamentos[i] : null;
        if (close == null) continue;
        final dataObj = DateTime.fromMillisecondsSinceEpoch((ts as num).toInt() * 1000);
        final abertura = i < aberturas.length ? aberturas[i] : null;
        final volume = i < volumes.length ? volumes[i] : null;
        pontos.add(
          PontoHistorico(
            dataIso: dataObj.toIso8601String().split('T').first,
            data: _dataParaExibicao(dataObj),
            precoFechamento: double.parse((close as num).toDouble().toStringAsFixed(2)),
            precoAbertura: abertura != null
                ? double.parse((abertura as num).toDouble().toStringAsFixed(2))
                : null,
            volume: volume != null ? (volume as num).toInt() : null,
          ),
        );
      }
      if (pontos.isEmpty) return null;
      return SerieHistorica(simbolo: simbolo, periodo: rotulo, pontos: pontos);
    } catch (_) {
      return null;
    }
  }

  String _dataParaExibicao(DateTime data) {
    if (data.hour == 0 && data.minute == 0) {
      return DateFormat('dd/MM/yyyy').format(data);
    }
    return DateFormat('dd/MM/yyyy HH:mm').format(data);
  }
}
