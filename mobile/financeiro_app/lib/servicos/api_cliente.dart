import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import '../modelos/cotacao_resumo.dart';
import '../modelos/resultado_busca.dart';

class ApiCliente {
  ApiCliente({http.Client? cliente}) : _cliente = cliente ?? http.Client();

  final http.Client _cliente;

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
  }

  Future<Map<String, List<CotacaoResumo>>> obterPainel({int quantidade = 10}) async {
    final uri = Uri.parse(
      ApiConfig.montarUrl('/api/mercado/painel?quantidade=$quantidade'),
    );
    final resposta = await _cliente.get(uri, headers: _cabecalhos());
    if (resposta.statusCode != 200) {
      throw Exception(_extrairErro(resposta));
    }

    final json = jsonDecode(resposta.body) as Map<String, dynamic>;
    return {
      'emAlta': _listaCotacoes(json['emAlta']),
      'emQueda': _listaCotacoes(json['emQueda']),
      'todas': _listaCotacoes(json['todas']),
    };
  }

  Future<CotacaoResumo> obterCotacao(String simbolo) async {
    final uri = Uri.parse(
      ApiConfig.montarUrl('/api/mercado/cotacao/${Uri.encodeComponent(simbolo)}'),
    );
    final resposta = await _cliente.get(uri, headers: _cabecalhos());
    if (resposta.statusCode != 200) {
      throw Exception(_extrairErro(resposta));
    }
    final json = jsonDecode(resposta.body) as Map<String, dynamic>;
    return CotacaoResumo.fromJson(json['cotacao'] as Map<String, dynamic>);
  }

  Future<List<ResultadoBusca>> buscarAcoes(String termo) async {
    final uri = Uri.parse(
      ApiConfig.montarUrl('/api/busca/acoes?q=${Uri.encodeQueryComponent(termo)}'),
    );
    final resposta = await _cliente.get(uri, headers: _cabecalhos());
    if (resposta.statusCode != 200) {
      throw Exception(_extrairErro(resposta));
    }
    final json = jsonDecode(resposta.body) as Map<String, dynamic>;
    final lista = json['resultados'] as List<dynamic>? ?? [];
    return lista
        .map((item) => ResultadoBusca.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  List<CotacaoResumo> _listaCotacoes(dynamic valor) {
    final lista = valor as List<dynamic>? ?? [];
    return lista
        .map((item) => CotacaoResumo.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  String _extrairErro(http.Response resposta) {
    try {
      final json = jsonDecode(resposta.body) as Map<String, dynamic>;
      return json['detail']?.toString() ?? 'Erro ${resposta.statusCode}';
    } catch (_) {
      return 'Erro ${resposta.statusCode}';
    }
  }
}
