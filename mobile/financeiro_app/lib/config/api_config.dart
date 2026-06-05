/// URL base da API (local ou Render).
class ApiConfig {
  /// Altere apos deploy no Render, ex.: https://financeiro-api.onrender.com
  static const String urlBasePadrao = 'http://10.0.2.2:8000';

  /// Chave opcional (mesmo valor de FINANCEIRO_API_KEY no servidor).
  static const String chaveApi = '';

  static String montarUrl(String caminho) {
    final base = urlBasePadrao.replaceAll(RegExp(r'/+$'), '');
    final path = caminho.startsWith('/') ? caminho : '/$caminho';
    return '$base$path';
  }
}
