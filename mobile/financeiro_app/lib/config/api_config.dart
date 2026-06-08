/// URL base da API (local ou Render).
class ApiConfig {
  /// Emulador: 127.0.0.1 com adb reverse (testar_apk.bat configura automaticamente).
  static const String urlBasePadrao = 'http://127.0.0.1:8000';

  /// Celular / producao no Render (use antes de gerar_apk.bat para o celular):
  /// 'https://windows-aplicacao-financeira.onrender.com'

  /// Chave opcional (mesmo valor de FINANCEIRO_API_KEY no servidor).
  static const String chaveApi = '';

  static String montarUrl(String caminho) {
    final base = urlBasePadrao.replaceAll(RegExp(r'/+$'), '');
    final path = caminho.startsWith('/') ? caminho : '/$caminho';
    return '$base$path';
  }
}
