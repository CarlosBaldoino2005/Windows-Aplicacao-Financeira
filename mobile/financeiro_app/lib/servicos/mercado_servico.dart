import '../dados/universo_mercado.dart';
import '../modelos/cotacao_resumo.dart';
import '../modelos/serie_historica.dart';
import '../modelos/tipo_ativo.dart';
import '../util/normalizacao_simbolo.dart';
import 'cadeia_mercado.dart';

/// Regras de negocio para painel, cotacao e historico (como o desktop).
class MercadoServico {
  MercadoServico({CadeiaMercado? cadeia}) : _cadeia = cadeia ?? CadeiaMercado();

  final CadeiaMercado _cadeia;
  static const int tamanhoLote = 25;

  Future<Map<String, List<CotacaoResumo>>> obterPainel({
    required TipoAtivo tipo,
    int quantidade = 10,
  }) async {
    switch (tipo) {
      case TipoAtivo.cripto:
        return _montarPainelCripto(quantidade);
      case TipoAtivo.fiis:
        return _montarPainelFiis(quantidade);
      case TipoAtivo.indices:
        return _montarPainelIndices(quantidade);
      case TipoAtivo.acoes:
        return _montarPainelAcoes(quantidade);
    }
  }

  Future<CotacaoResumo> obterCotacao(String simbolo, TipoAtivo tipo) async {
    final simboloOk = _normalizarPorTipo(simbolo, tipo);
    final resumos = await buscarResumos([simboloOk]);
    if (resumos.isEmpty) {
      throw Exception('Cotacao indisponivel para $simboloOk.');
    }
    return resumos.first;
  }

  Future<SerieHistorica> obterHistorico(
    String simbolo,
    TipoAtivo tipo, {
    String periodo = 'mes',
  }) async {
    final simboloOk = _normalizarPorTipo(simbolo, tipo);
    final serie = await _cadeia.buscarHistorico(simboloOk, periodo);
    if (serie == null || serie.pontos.isEmpty) {
      throw Exception('Historico indisponivel para $simboloOk.');
    }
    return serie;
  }

  Future<List<CotacaoResumo>> buscarResumos(List<String> simbolos) async {
    if (simbolos.isEmpty) return [];
    if (simbolos.length <= tamanhoLote) {
      return _cadeia.buscarResumos(simbolos);
    }
    final agregado = <CotacaoResumo>[];
    for (var inicio = 0; inicio < simbolos.length; inicio += tamanhoLote) {
      final fim = (inicio + tamanhoLote).clamp(0, simbolos.length);
      final lote = simbolos.sublist(inicio, fim);
      agregado.addAll(await _cadeia.buscarResumos(lote));
    }
    return agregado;
  }

  Future<Map<String, List<CotacaoResumo>>> _montarPainelAcoes(int quantidade) async {
    final simbolos = UniversoMercado.montarAcoesMonitoradas(quantidade);
    final resumos = await buscarResumos(simbolos);
    return _ordenarPainel(resumos, quantidade);
  }

  Future<Map<String, List<CotacaoResumo>>> _montarPainelCripto(int quantidade) async {
    final simbolos = UniversoMercado.montarCriptoMonitoradas(quantidade);
    final resumosBrutos = await buscarResumos(simbolos);
    final resumos = resumosBrutos.map((r) {
      final nome = UniversoMercado.nomesCripto[r.simbolo];
      if (nome != null && (r.nome.isEmpty || r.nome == r.simbolo)) {
        return CotacaoResumo(
          simbolo: r.simbolo,
          codigo: r.codigo,
          nome: nome,
          preco: r.preco,
          variacaoPercentual: r.variacaoPercentual,
          variacaoValor: r.variacaoValor,
          moeda: r.moeda,
          volume: r.volume,
        );
      }
      return r;
    }).toList();
    return _ordenarPainel(resumos, quantidade);
  }

  Future<Map<String, List<CotacaoResumo>>> _montarPainelFiis(int quantidade) async {
    final simbolos = UniversoMercado.montarFiisMonitorados(quantidade);
    final resumos = await buscarResumos(simbolos);
    return _ordenarPainel(resumos, quantidade);
  }

  Future<Map<String, List<CotacaoResumo>>> _montarPainelIndices(int quantidade) async {
    final simbolos = UniversoMercado.montarIndices(quantidade);
    final resumos = await buscarResumos(simbolos);
    final nomes = {for (final i in UniversoMercado.indices) i.simbolo: i.nome};

    final ajustados = resumos.map((r) {
      final nomeIndice = nomes[r.simbolo];
      if (nomeIndice != null && (r.nome.isEmpty || r.nome == r.simbolo)) {
        return CotacaoResumo(
          simbolo: r.simbolo,
          codigo: r.codigo,
          nome: nomeIndice,
          preco: r.preco,
          variacaoPercentual: r.variacaoPercentual,
          variacaoValor: r.variacaoValor,
          moeda: r.moeda,
          volume: r.volume,
        );
      }
      return r;
    }).toList();

    final emAlta = ajustados.where((r) => r.variacaoPercentual > 0).toList()
      ..sort((a, b) => b.variacaoPercentual.compareTo(a.variacaoPercentual));
    final emQueda = ajustados.where((r) => r.variacaoPercentual < 0).toList()
      ..sort((a, b) => a.variacaoPercentual.compareTo(b.variacaoPercentual));
    final todas = List<CotacaoResumo>.from(ajustados)
      ..sort((a, b) => (nomes[a.simbolo] ?? a.simbolo).compareTo(nomes[b.simbolo] ?? b.simbolo));

    return {
      'emAlta': emAlta.take(quantidade).toList(),
      'emQueda': emQueda.take(quantidade).toList(),
      'todas': todas.take(quantidade).toList(),
    };
  }

  Map<String, List<CotacaoResumo>> _ordenarPainel(List<CotacaoResumo> resumos, int quantidade) {
    final emAlta = resumos.where((r) => r.variacaoPercentual > 0).toList()
      ..sort((a, b) => b.variacaoPercentual.compareTo(a.variacaoPercentual));
    final emQueda = resumos.where((r) => r.variacaoPercentual < 0).toList()
      ..sort((a, b) => a.variacaoPercentual.compareTo(b.variacaoPercentual));
    final todas = List<CotacaoResumo>.from(resumos)..sort((a, b) => a.simbolo.compareTo(b.simbolo));
    return {
      'emAlta': emAlta.take(quantidade).toList(),
      'emQueda': emQueda.take(quantidade).toList(),
      'todas': todas.take(quantidade).toList(),
    };
  }

  String _normalizarPorTipo(String simbolo, TipoAtivo tipo) {
    switch (tipo) {
      case TipoAtivo.cripto:
        final ok = NormalizacaoSimbolo.normalizarCripto(simbolo);
        if (ok.erro != null) throw Exception(ok.erro);
        return ok.simbolo!;
      case TipoAtivo.fiis:
        final ok = NormalizacaoSimbolo.normalizarAcao(simbolo);
        if (ok.erro != null) throw Exception(ok.erro);
        if (!NormalizacaoSimbolo.ehFii(ok.simbolo!)) {
          throw Exception('Codigo informado nao e um fundo imobiliario (FII).');
        }
        return ok.simbolo!;
      case TipoAtivo.indices:
        final ok = NormalizacaoSimbolo.normalizarIndice(simbolo);
        if (ok == null) throw Exception('Indice nao reconhecido.');
        return ok;
      case TipoAtivo.acoes:
        final ok = NormalizacaoSimbolo.normalizarAcao(simbolo);
        if (ok.erro != null) throw Exception(ok.erro);
        return ok.simbolo!;
    }
  }
}
