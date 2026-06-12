import 'package:intl/intl.dart';

import '../../modelos/cotacao_resumo.dart';
import '../../modelos/serie_historica.dart';
import '../../util/mapeamento_periodo.dart';
import '../../util/normalizacao_simbolo.dart';
import 'requisicao_provedor.dart';

/// Cotacoes e historico para tickers .SA via brapi.dev.
class BrapiProvedor {
  BrapiProvedor({RequisicaoProvedor? requisicao, this.tokenBrapi = ''})
      : _requisicao = requisicao ?? RequisicaoProvedor();

  final RequisicaoProvedor _requisicao;
  final String tokenBrapi;
  static const String urlBase = 'https://brapi.dev/api';

  Future<List<CotacaoResumo>> buscarResumos(List<String> simbolos) async {
    final b3 = simbolos.where(NormalizacaoSimbolo.ehAcaoB3).toList();
    if (b3.isEmpty) return [];

    final codigos = b3.map(NormalizacaoSimbolo.codigoBrapi).join(',');
    final dados = await _requisicao.getJson(
      '$urlBase/quote/${Uri.encodeComponent(codigos)}',
      tokenBrapi: tokenBrapi,
    );
    if (dados == null) return [];

    final mapaSimbolo = {for (final s in b3) NormalizacaoSimbolo.codigoBrapi(s): s};
    final resultados = <CotacaoResumo>[];
    for (final item in (dados['results'] as List<dynamic>? ?? [])) {
      if (item is! Map<String, dynamic>) continue;
      final codigo = item['symbol']?.toString().toUpperCase() ?? '';
      final simbolo = mapaSimbolo[codigo];
      if (simbolo == null) continue;
      final resumo = _itemParaResumo(simbolo, item);
      if (resumo != null) resultados.add(resumo);
    }
    return resultados;
  }

  Future<SerieHistorica?> buscarHistorico(String simbolo, String periodoChave) async {
    if (!NormalizacaoSimbolo.ehAcaoB3(simbolo)) return null;

    final cfg = MapeamentoPeriodo.brapi[periodoChave] ?? MapeamentoPeriodo.brapi['mes']!;
    final codigo = NormalizacaoSimbolo.codigoBrapi(simbolo);
    final url =
        '$urlBase/quote/${Uri.encodeComponent(codigo)}?range=${cfg['range']}&interval=${cfg['interval']}';
    final dados = await _requisicao.getJson(url, tokenBrapi: tokenBrapi);
    if (dados == null) return null;

    final resultados = dados['results'] as List<dynamic>?;
    if (resultados == null || resultados.isEmpty) return null;
    final primeiro = resultados.first;
    if (primeiro is! Map<String, dynamic>) return null;

    final historico = primeiro['historicalDataPrice'] as List<dynamic>? ?? [];
    final pontos = <PontoHistorico>[];
    for (final barra in historico) {
      if (barra is! Map<String, dynamic>) continue;
      final ts = barra['date'];
      if (ts == null) continue;
      final dataObj = DateTime.fromMillisecondsSinceEpoch((ts as num).toInt() * 1000);
      pontos.add(
        PontoHistorico(
          dataIso: dataObj.toIso8601String().split('T').first,
          data: DateFormat('dd/MM/yyyy').format(dataObj),
          precoFechamento: double.parse((barra['close'] as num).toDouble().toStringAsFixed(2)),
          precoAbertura: double.parse((barra['open'] as num).toDouble().toStringAsFixed(2)),
          volume: (barra['volume'] as num?)?.toInt(),
        ),
      );
    }

    final diasRecorte = MapeamentoPeriodo.diasDoPeriodo(cfg);
    if (diasRecorte != null) {
      final limite = DateTime.now().subtract(Duration(days: diasRecorte));
      pontos.removeWhere((p) {
        final data = DateTime.tryParse(p.dataIso);
        return data == null || data.isBefore(limite);
      });
    }

    if (pontos.isEmpty) return null;
    return SerieHistorica(simbolo: simbolo, periodo: periodoChave, pontos: pontos);
  }

  Future<Map<String, dynamic>?> buscarCotacaoDetalhe(String simbolo) async {
    if (!NormalizacaoSimbolo.ehAcaoB3(simbolo)) return null;
    final codigo = NormalizacaoSimbolo.codigoBrapi(simbolo);
    return _requisicao.getJson(
      '$urlBase/quote/${Uri.encodeComponent(codigo)}',
      tokenBrapi: tokenBrapi,
    );
  }

  CotacaoResumo? _itemParaResumo(String simbolo, Map<String, dynamic> item) {
    final precoBruto = item['regularMarketPrice'];
    if (precoBruto is! num) return null;
    final preco = precoBruto.toDouble();
    final variacaoPct = (item['regularMarketChangePercent'] as num?)?.toDouble() ?? 0;
    final anterior = item['regularMarketPreviousClose'];
    final variacaoValor = anterior is num
        ? preco - anterior.toDouble()
        : preco * (variacaoPct / 100);
    final volume = item['regularMarketVolume'];
    return CotacaoResumo(
      simbolo: simbolo,
      codigo: simbolo.replaceAll('.SA', ''),
      nome: item['shortName']?.toString() ??
          item['longName']?.toString() ??
          simbolo.replaceAll('.SA', ''),
      preco: double.parse(preco.toStringAsFixed(2)),
      variacaoPercentual: double.parse(variacaoPct.toStringAsFixed(2)),
      variacaoValor: double.parse(variacaoValor.toStringAsFixed(2)),
      volume: volume is num ? volume.toInt() : null,
      moeda: item['currency']?.toString() ?? 'BRL',
    );
  }
}
