/// URL base da API FastAPI local (sem Render / nuvem).
class ApiConfig {
  /// Padrao emulador com adb reverse (testar_apk.bat).
  static const String urlApiLocalPadrao = 'http://127.0.0.1:8000';

  /// Celular fisico: IP do PC na Wi-Fi (gerar_apk.bat via celular_api_url.bat).
  static const String urlApiCelularExemplo = 'http://192.168.0.10:8000';

  /// Sobrescrito no build: --dart-define=API_BASE_URL=...
  static const String urlBasePadrao = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: urlApiLocalPadrao,
  );

  /// Chave opcional (FINANCEIRO_API_KEY no servidor, se configurada).
  static const String chaveApi = '';

  static String montarUrl(String caminho) {
    final base = urlBasePadrao.replaceAll(RegExp(r'/+$'), '');
    final path = caminho.startsWith('/') ? caminho : '/$caminho';
    return '$base$path';
  }

  static bool get usaLocalhost =>
      urlBasePadrao.contains('127.0.0.1') || urlBasePadrao.contains('localhost');

  static String mensagemErroConexao(Object erro) {
    final detalhe = erro.toString().replaceFirst('Exception: ', '');
    final buffer = StringBuffer()
      ..writeln('Nao foi possivel conectar a API local.')
      ..writeln('URL: $urlBasePadrao')
      ..writeln()
      ..writeln('1. No PC, execute executar_api.bat e deixe a janela aberta.')
      ..writeln('2. Celular e PC na mesma rede Wi-Fi.')
      ..writeln('3. Gere o APK com mobile\\gerar_apk.bat (IP em celular_api_url.bat).')
      ..writeln('4. Emulador: gerar_apk_emulador.bat + testar_apk.bat.')
      ..writeln();

    if (usaLocalhost) {
      buffer.writeln(
        'No celular fisico, 127.0.0.1 e o proprio aparelho — use o IP do PC em celular_api_url.bat.',
      );
      buffer.writeln();
    }

    buffer.write(detalhe);
    return buffer.toString();
  }
}
