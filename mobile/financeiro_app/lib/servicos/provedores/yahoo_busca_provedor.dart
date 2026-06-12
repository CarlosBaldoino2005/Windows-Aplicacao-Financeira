import '../../modelos/resultado_busca.dart';
import '../../util/normalizacao_simbolo.dart';
import 'requisicao_provedor.dart';

/// Busca de tickers via API de pesquisa do Yahoo Finance.
class YahooBuscaProvedor {
  YahooBuscaProvedor({RequisicaoProvedor? requisicao})
      : _requisicao = requisicao ?? RequisicaoProvedor();

  final RequisicaoProvedor _requisicao;
  static const String urlBusca =
      'https://query2.finance.yahoo.com/v1/finance/search';

  Future<List<ResultadoBusca>> buscarAcoes(String termo, int limite) async {
    final dados = await _buscar(termo, limite * 2);
    if (dados == null) return [];

    final resultados = <ResultadoBusca>[];
    final vistos = <String>{};
    for (final item in dados) {
      if (item['quoteType'] != 'EQUITY' && item['quoteType'] != 'ETF') continue;
      final simboloBruto = item['symbol']?.toString().trim().toUpperCase() ?? '';
      if (simboloBruto.isEmpty) continue;
      if (simboloBruto.endsWith('.BA') || simboloBruto.endsWith('.MX')) continue;

      final nome = item['longname']?.toString() ??
          item['shortname']?.toString() ??
          simboloBruto;
      String bolsa;
      String simboloFinal;

      if (simboloBruto.endsWith('.SA')) {
        if (!RegExp(r'^[A-Z]{3,5}\d{1,2}\.SA$').hasMatch(simboloBruto)) continue;
        bolsa = 'B3';
        simboloFinal = simboloBruto;
      } else if (RegExp(r'^[A-Z]{1,5}$').hasMatch(simboloBruto)) {
        bolsa = 'EUA';
        simboloFinal = simboloBruto;
      } else {
        continue;
      }

      if (!vistos.add(simboloFinal)) continue;
      resultados.add(ResultadoBusca(
        simbolo: simboloFinal,
        codigo: simboloFinal.replaceAll('.SA', ''),
        nome: nome,
        bolsa: bolsa,
      ));
      if (resultados.length >= limite) break;
    }
    return resultados;
  }

  Future<List<ResultadoBusca>> buscarCripto(String termo, int limite) async {
    final dados = await _buscar(termo, limite * 3);
    if (dados == null) return [];

    final resultados = <ResultadoBusca>[];
    final vistos = <String>{};
    for (final item in dados) {
      if (item['quoteType'] != 'CRYPTOCURRENCY') continue;
      final simboloBruto = item['symbol']?.toString().trim().toUpperCase() ?? '';
      final normalizado = NormalizacaoSimbolo.normalizarCripto(simboloBruto);
      if (normalizado.erro != null || normalizado.simbolo == null) continue;
      if (!vistos.add(normalizado.simbolo!)) continue;
      final nome = item['longname']?.toString() ??
          item['shortname']?.toString() ??
          normalizado.simbolo!;
      resultados.add(ResultadoBusca(
        simbolo: normalizado.simbolo!,
        codigo: normalizado.simbolo!.replaceAll('-USD', ''),
        nome: nome,
        bolsa: 'Cripto',
      ));
      if (resultados.length >= limite) break;
    }
    return resultados;
  }

  Future<List<dynamic>?> _buscar(String termo, int limite) async {
    final url =
        '$urlBusca?q=${Uri.encodeQueryComponent(termo)}&quotesCount=$limite&newsCount=0';
    final dados = await _requisicao.getJson(url);
    if (dados == null) return null;
    return dados['quotes'] as List<dynamic>?;
  }
}
