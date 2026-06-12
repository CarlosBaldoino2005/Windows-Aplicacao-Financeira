import '../dados/universo_mercado.dart';
import '../modelos/detalhes_ativo.dart';
import '../modelos/tipo_ativo.dart';
import '../util/normalizacao_simbolo.dart';
import 'provedores/brapi_provedor.dart';
import 'provedores/requisicao_provedor.dart';
import 'provedores/yahoo_chart_provedor.dart';

/// Detalhes do ativo via Yahoo Quote Summary, Brapi e Yahoo Chart.
class DetalhesMercadoServico {
  DetalhesMercadoServico({
    RequisicaoProvedor? requisicao,
    BrapiProvedor? brapi,
    YahooChartProvedor? yahooChart,
  })  : _requisicao = requisicao ?? RequisicaoProvedor(),
        _brapi = brapi ?? BrapiProvedor(),
        _yahooChart = yahooChart ?? YahooChartProvedor();

  final RequisicaoProvedor _requisicao;
  final BrapiProvedor _brapi;
  final YahooChartProvedor _yahooChart;

  static const String urlQuoteSummary =
      'https://query1.finance.yahoo.com/v10/finance/quoteSummary';

  Future<DetalhesAtivo> obterDetalhes(String simbolo, TipoAtivo tipo) async {
    if (tipo == TipoAtivo.cripto) {
      return _obterDetalhesCripto(simbolo);
    }
    if (tipo == TipoAtivo.fiis) {
      final ok = NormalizacaoSimbolo.normalizarAcao(simbolo);
      if (ok.erro != null) throw Exception(ok.erro);
      if (!NormalizacaoSimbolo.ehFii(ok.simbolo!)) {
        throw Exception('Codigo informado nao e um fundo imobiliario (FII).');
      }
      return _obterDetalhesAcao(ok.simbolo!);
    }
    if (tipo == TipoAtivo.indices) {
      final ok = NormalizacaoSimbolo.normalizarIndice(simbolo);
      if (ok == null) throw Exception('Indice nao reconhecido.');
      return _obterDetalhesAcao(ok);
    }
    final ok = NormalizacaoSimbolo.normalizarAcao(simbolo);
    if (ok.erro != null) throw Exception(ok.erro);
    return _obterDetalhesAcao(ok.simbolo!);
  }

  Future<DetalhesAtivo> _obterDetalhesCripto(String simbolo) async {
    final ok = NormalizacaoSimbolo.normalizarCripto(simbolo);
    if (ok.erro != null) throw Exception(ok.erro);
    final simboloOk = ok.simbolo!;

    final detalhesYahoo = await _tentarQuoteSummary(simboloOk, ehCripto: true);
    if (detalhesYahoo != null) return detalhesYahoo;

    final meta = await _yahooChart.buscarMeta(simboloOk);
    if (meta != null) {
      final codigo = simboloOk.replaceAll('-USD', '');
      return DetalhesAtivo(
        simbolo: simboloOk,
        codigo: codigo,
        moeda: meta['currency']?.toString() ?? 'USD',
        nomeEmpresa: meta['longName']?.toString() ??
            meta['shortName']?.toString() ??
            UniversoMercado.nomesCripto[simboloOk] ??
            codigo,
        precoAtual: (meta['regularMarketPrice'] as num?)?.toDouble(),
        variacaoDiaPct: null,
        ehCripto: true,
        avisos: const ['Dados basicos via Yahoo Chart API.'],
      );
    }
    throw Exception('Nao foi possivel carregar detalhes da criptomoeda.');
  }

  Future<DetalhesAtivo> _obterDetalhesAcao(String simbolo) async {
    final detalhesYahoo = await _tentarQuoteSummary(simbolo, ehCripto: false);
    if (detalhesYahoo != null) {
      return detalhesYahoo;
    }

    if (NormalizacaoSimbolo.ehAcaoB3(simbolo)) {
      final detalhesBrapi = await _montarDeBrapi(simbolo);
      if (detalhesBrapi != null) return detalhesBrapi;
    }

    final meta = await _yahooChart.buscarMeta(simbolo);
    if (meta != null) {
      return DetalhesAtivo(
        simbolo: simbolo,
        codigo: simbolo.replaceAll('.SA', ''),
        moeda: meta['currency']?.toString() ?? (simbolo.endsWith('.SA') ? 'BRL' : 'USD'),
        nomeEmpresa: meta['longName']?.toString() ??
            meta['shortName']?.toString() ??
            simbolo.replaceAll('.SA', ''),
        precoAtual: (meta['regularMarketPrice'] as num?)?.toDouble(),
        avisos: const [
          'Yahoo indisponivel. Dados basicos via Yahoo Chart API.',
        ],
      );
    }

    throw Exception(
      'Nao foi possivel carregar detalhes. Verifique sua conexao e tente novamente.',
    );
  }

  Future<DetalhesAtivo?> _tentarQuoteSummary(String simbolo, {required bool ehCripto}) async {
    final modulos = ehCripto
        ? 'summaryProfile,financialData,defaultKeyStatistics,summaryDetail'
        : 'assetProfile,summaryProfile,financialData,defaultKeyStatistics,'
            'recommendationTrend,calendarEvents,'
            'incomeStatementHistory,incomeStatementHistoryQuarterly,summaryDetail';
    final url =
        '$urlQuoteSummary/${Uri.encodeComponent(simbolo)}?modules=$modulos';
    final dados = await _requisicao.getJson(url);
    if (dados == null) return null;

    try {
      final resultados = dados['quoteSummary']?['result'] as List<dynamic>?;
      if (resultados == null || resultados.isEmpty) return null;
      final bloco = resultados.first as Map<String, dynamic>;

      final perfil = bloco['assetProfile'] as Map<String, dynamic>? ??
          bloco['summaryProfile'] as Map<String, dynamic>? ??
          {};
      final financeiro = bloco['financialData'] as Map<String, dynamic>? ?? {};
      final estatisticas = bloco['defaultKeyStatistics'] as Map<String, dynamic>? ?? {};
      final resumo = bloco['summaryDetail'] as Map<String, dynamic>? ?? {};

      final moeda = simbolo.endsWith('.SA') ? 'BRL' : (resumo['currency']?.toString() ?? 'USD');
      final codigo = simbolo.replaceAll('.SA', '').replaceAll('-USD', '');
      final preco = _extrairRaw(resumo['regularMarketPrice']) ??
          _extrairRaw(financeiro['currentPrice']);

      final indicadores = <Map<String, String>>[];
      void addIndicador(String rotulo, dynamic valor) {
        final texto = _formatarIndicador(valor, moeda);
        if (texto != null) indicadores.add({'rotulo': rotulo, 'valor': texto});
      }

      addIndicador('Preco atual', preco);
      addIndicador('P/L', _extrairRaw(estatisticas['trailingPE']));
      addIndicador('ROE', _extrairRaw(financeiro['returnOnEquity']));
      addIndicador('Dividend yield', _extrairRaw(resumo['dividendYield']));
      addIndicador('Beta', _extrairRaw(estatisticas['beta']));
      addIndicador('Market cap', _extrairRaw(estatisticas['marketCap']));

      final trimestres = _extrairDemonstrativos(bloco['incomeStatementHistoryQuarterly']);
      final anuais = _extrairDemonstrativos(bloco['incomeStatementHistory']);
      final opinioes = _extrairOpinioes(bloco['recommendationTrend']);

      return DetalhesAtivo(
        simbolo: simbolo,
        codigo: codigo,
        moeda: moeda,
        nomeEmpresa: perfil['longName']?.toString() ??
            perfil['name']?.toString() ??
            resumo['longName']?.toString() ??
            codigo,
        setor: perfil['sector']?.toString() ?? '',
        industria: perfil['industry']?.toString() ?? '',
        pais: perfil['country']?.toString() ?? '',
        site: perfil['website']?.toString() ?? '',
        descricao: perfil['longBusinessSummary']?.toString() ?? '',
        funcionarios: (perfil['fullTimeEmployees'] as num?)?.toInt(),
        precoAtual: preco,
        variacaoDiaPct: null,
        indicadores: indicadores,
        trimestres: trimestres,
        anuais: anuais,
        opinioesAnalistas: opinioes,
        ehCripto: ehCripto,
        avisos: const ['Dados carregados via Yahoo Finance.'],
      );
    } catch (_) {
      return null;
    }
  }

  Future<DetalhesAtivo?> _montarDeBrapi(String simbolo) async {
    final dados = await _brapi.buscarCotacaoDetalhe(simbolo);
    if (dados == null) return null;
    final resultados = dados['results'] as List<dynamic>?;
    if (resultados == null || resultados.isEmpty) return null;
    final item = resultados.first as Map<String, dynamic>;
    final codigo = simbolo.replaceAll('.SA', '');
    final preco = (item['regularMarketPrice'] as num?)?.toDouble();
    final variacaoPct = (item['regularMarketChangePercent'] as num?)?.toDouble();

    final indicadores = <Map<String, String>>[];
    if (preco != null) {
      indicadores.add({'rotulo': 'Preco atual', 'valor': preco.toStringAsFixed(2)});
    }
    if (variacaoPct != null) {
      indicadores.add({'rotulo': 'Variacao do dia', 'valor': '${variacaoPct.toStringAsFixed(2)}%'});
    }

    return DetalhesAtivo(
      simbolo: simbolo,
      codigo: codigo,
      moeda: item['currency']?.toString() ?? 'BRL',
      nomeEmpresa: item['longName']?.toString() ??
          item['shortName']?.toString() ??
          codigo,
      pais: 'Brasil',
      precoAtual: preco,
      variacaoDiaPct: variacaoPct,
      indicadores: indicadores,
      avisos: const [
        'Yahoo indisponivel. Dados basicos via Brapi.',
        'Demonstrativos completos podem estar limitados.',
      ],
    );
  }

  List<Map<String, dynamic>> _extrairDemonstrativos(dynamic bloco) {
    if (bloco is! Map<String, dynamic>) return [];
    final lista = bloco['incomeStatementHistory'] as List<dynamic>? ??
        bloco['incomeStatementHistoryQuarterly'] as List<dynamic>? ??
        [];
    final resultado = <Map<String, dynamic>>[];
    for (final item in lista) {
      if (item is! Map<String, dynamic>) continue;
      final data = item['endDate'];
      final periodo = data is Map ? data['fmt']?.toString() ?? '' : data?.toString() ?? '';
      resultado.add({
        'periodo': periodo,
        'receita': _extrairRaw(item['totalRevenue']),
        'lucroLiquido': _extrairRaw(item['netIncome']),
        'ebitda': _extrairRaw(item['ebitda']),
        'lucroOperacional': _extrairRaw(item['operatingIncome']),
      });
    }
    return resultado;
  }

  Map<String, dynamic>? _extrairOpinioes(dynamic bloco) {
    if (bloco is! Map<String, dynamic>) return null;
    final tendencias = bloco['trend'] as List<dynamic>?;
    if (tendencias == null || tendencias.isEmpty) return null;
    final atual = tendencias.first;
    if (atual is! Map<String, dynamic>) return null;
    return {
      'notaMedia': (atual['strongBuy'] as num? ?? 0) + (atual['buy'] as num? ?? 0),
      'compraForte': atual['strongBuy'],
      'compra': atual['buy'],
      'manter': atual['hold'],
      'vender': atual['sell'],
      'vendaForte': atual['strongSell'],
      'totalAnalistas': atual['numberOfAnalysts'],
    };
  }

  double? _extrairRaw(dynamic valor) {
    if (valor is num) return valor.toDouble();
    if (valor is Map && valor['raw'] is num) return (valor['raw'] as num).toDouble();
    return null;
  }

  String? _formatarIndicador(dynamic valor, String moeda) {
    final numero = _extrairRaw(valor);
    if (numero == null) return null;
    if (numero > 1000000) return numero.toStringAsFixed(0);
    if (numero < 1 && numero > 0) return '${(numero * 100).toStringAsFixed(2)}%';
    return numero.toStringAsFixed(2);
  }
}
