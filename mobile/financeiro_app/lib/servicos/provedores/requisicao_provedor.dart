import 'dart:convert';

import 'package:http/http.dart' as http;

/// Requisições HTTP compartilhadas pelos provedores de mercado.
class RequisicaoProvedor {
  RequisicaoProvedor({http.Client? cliente}) : _cliente = cliente ?? http.Client();

  final http.Client _cliente;

  static const Duration tempoLimite = Duration(seconds: 20);
  static const String userAgent = 'Financeiro-Mobile/1.1';

  Future<Map<String, dynamic>?> getJson(String url, {String? tokenBrapi}) async {
    final cabecalhos = <String, String>{
      'Accept': 'application/json',
      'User-Agent': userAgent,
    };
    if (tokenBrapi != null && tokenBrapi.isNotEmpty && url.contains('brapi.dev')) {
      cabecalhos['Authorization'] = 'Bearer $tokenBrapi';
    }

    try {
      final resposta = await _cliente
          .get(Uri.parse(url), headers: cabecalhos)
          .timeout(tempoLimite);
      if (resposta.statusCode != 200) return null;
      final decodificado = jsonDecode(resposta.body);
      if (decodificado is Map<String, dynamic>) return decodificado;
      return null;
    } catch (_) {
      return null;
    }
  }
}
