/// URL base da API (local ou Render).
class ApiConfig {
  /// API publicada no Render (producao).
  static const String urlBasePadrao = 'https://windows-aplicacao-financeira.onrender.com';

  /// Emulador Android com API local: 'http://10.0.2.2:8000'

  /// Chave opcional (mesmo valor de FINANCEIRO_API_KEY no servidor).
  static const String chaveApi = '';

  static String montarUrl(String caminho) {
    final base = urlBasePadrao.replaceAll(RegExp(r'/+$'), '');
    final path = caminho.startsWith('/') ? caminho : '/$caminho';
    return '$base$path';
  }
}
