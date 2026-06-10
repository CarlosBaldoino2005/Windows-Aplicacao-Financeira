import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import '../modelos/cotacao_resumo.dart';
import '../modelos/detalhes_ativo.dart';
import '../modelos/resultado_busca.dart';
import '../modelos/serie_historica.dart';
import '../modelos/tipo_ativo.dart';

class ApiCliente {
  ApiCliente({http.Client? cliente}) : _cliente = cliente ?? http.Client();

  final http.Client _cliente;

  /// Versao retornada por /api/saude (ex.: 1.1.0).
  static String versaoApi = '1.0.0';

  /// Recursos informados pela API apos o health check.
  static List<String> recursosApi = const [];

  static bool get suportaPainelCompleto =>
      _compararVersao(versaoApi, '1.1.0') >= 0 ||
      recursosApi.contains('painel-cripto');

  Map<String, String> _cabecalhos() {
    final mapa = <String, String>{'Accept': 'application/json'};
    if (ApiConfig.chaveApi.isNotEmpty) {
      mapa['X-API-Key'] = ApiConfig.chaveApi;
    }
    return mapa;
  }

  Future<void> verificarSaude() async {
    final resposta = await _cliente.get(
      Uri.parse(ApiConfig.montarUrl('/api/saude')),
      headers: _cabecalhos(),
    );
    if (resposta.statusCode != 200) {
      throw Exception('API indisponivel (${resposta.statusCode}).');
    }
    final json = jsonDecode(resposta.body) as Map<String, dynamic>;
    versaoApi = json['versao']?.toString() ?? '1.0.0';
    recursosApi = (json['recursos'] as List<dynamic>? ?? []).map((e) => e.toString()).toList();
  }

  static String mensagemApiDesatualizada(TipoAtivo tipo) {
    return 'A API está na versão $versaoApi e não suporta ${tipo.rotulo}.\n\n'
        'Atualize a API local (executar_api.bat) para a versão 1.1.0 ou superior.';
  }

  static bool tipoExigeApiRecente(TipoAtivo tipo) =>
      tipo != TipoAtivo.acoes && !suportaPainelCompleto;

  Future<Map<String, List<CotacaoResumo>>> obterPainel({
    TipoAtivo tipo = TipoAtivo.acoes,
    int quantidade = 10,
  }) async {
    if (tipoExigeApiRecente(tipo)) {
      throw Exception(mensagemApiDesatualizada(tipo));
    }

    final caminho =
        '/api/mercado/painel?quantidade=$quantidade&tipo=${Uri.encodeQueryComponent(tipo.chave)}';
    return _parsePainel(await _getJson(caminho));
  }

  Future<CotacaoResumo> obterCotacao(String simbolo, {TipoAtivo tipo = TipoAtivo.acoes}) async {
    if (tipoExigeApiRecente(tipo)) {
      throw Exception(mensagemApiDesatualizada(tipo));
    }

    final caminho =
        '/api/mercado/cotacao/${Uri.encodeComponent(simbolo)}?tipo=${Uri.encodeQueryComponent(tipo.chave)}';
    final json = await _getJson(caminho);
    return CotacaoResumo.fromJson(json['cotacao'] as Map<String, dynamic>);
  }

  Future<SerieHistorica> obterHistorico(
    String simbolo, {
    TipoAtivo tipo = TipoAtivo.acoes,
    String periodo = 'mes',
  }) async {
    if (tipoExigeApiRecente(tipo)) {
      throw Exception(mensagemApiDesatualizada(tipo));
    }

    final caminho = '/api/mercado/historico/${Uri.encodeComponent(simbolo)}'
        '?periodo=${Uri.encodeQueryComponent(periodo)}'
        '&tipo=${Uri.encodeQueryComponent(tipo.chave)}';
    final json = await _getJson(caminho);
    return SerieHistorica.fromJson(json['serie'] as Map<String, dynamic>);
  }

  Future<DetalhesAtivo> obterDetalhes(String simbolo, {TipoAtivo tipo = TipoAtivo.acoes}) async {
    if (tipoExigeApiRecente(tipo)) {
      throw Exception(mensagemApiDesatualizada(tipo));
    }

    final parametro = tipo.parametroDetalhes;
    final caminho =
        '/api/mercado/detalhes/${Uri.encodeComponent(simbolo)}?tipo=${Uri.encodeQueryComponent(parametro)}';
    final json = await _getJson(caminho);
    return DetalhesAtivo.fromJson(json['detalhes'] as Map<String, dynamic>);
  }

  Future<List<ResultadoBusca>> buscar(String termo, {TipoAtivo tipo = TipoAtivo.acoes}) async {
    if (tipoExigeApiRecente(tipo)) {
      throw Exception(mensagemApiDesatualizada(tipo));
    }

    final caminho = '/api/busca/acoes?q=${Uri.encodeQueryComponent(termo)}'
        '&tipo=${Uri.encodeQueryComponent(tipo.chave)}';
    final json = await _getJson(caminho);
    final lista = json['resultados'] as List<dynamic>? ?? [];
    return lista
        .map((item) => ResultadoBusca.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<Map<String, dynamic>> _getJson(String caminho) async {
    final resposta = await _cliente.get(
      Uri.parse(ApiConfig.montarUrl(caminho)),
      headers: _cabecalhos(),
    );
    if (resposta.statusCode != 200) {
      throw Exception(_extrairErro(resposta));
    }
    return jsonDecode(resposta.body) as Map<String, dynamic>;
  }

  Map<String, List<CotacaoResumo>> _parsePainel(Map<String, dynamic> json) {
    return {
      'emAlta': _listaCotacoes(json['emAlta']),
      'emQueda': _listaCotacoes(json['emQueda']),
      'todas': _listaCotacoes(json['todas']),
    };
  }

  List<CotacaoResumo> _listaCotacoes(dynamic valor) {
    final lista = valor as List<dynamic>? ?? [];
    return lista
        .map((item) => CotacaoResumo.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  String _extrairErro(http.Response resposta) {
    if (resposta.statusCode == 404) {
      return 'Recurso não encontrado na API (${resposta.statusCode}). '
          'Verifique se a API está na versão 1.1.0 ou superior.';
    }
    try {
      final json = jsonDecode(resposta.body) as Map<String, dynamic>;
      final detalhe = json['detail']?.toString();
      if (detalhe != null && detalhe.isNotEmpty) return detalhe;
      return 'Erro ${resposta.statusCode}';
    } catch (_) {
      return 'Erro ${resposta.statusCode}';
    }
  }

  static int _compararVersao(String atual, String minima) {
    final partesAtual = atual.split('.').map(int.tryParse).toList();
    final partesMinima = minima.split('.').map(int.tryParse).toList();
    for (var i = 0; i < 3; i++) {
      final a = i < partesAtual.length ? (partesAtual[i] ?? 0) : 0;
      final b = i < partesMinima.length ? (partesMinima[i] ?? 0) : 0;
      if (a != b) return a.compareTo(b);
    }
    return 0;
  }
}
