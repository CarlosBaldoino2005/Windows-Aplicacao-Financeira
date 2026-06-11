/// URL base da API local (PC na mesma rede Wi-Fi ou emulador).
class ApiConfig {
  /// Emulador Android no PC (com adb reverse).
  static const String urlEmulador = 'http://127.0.0.1:8000';

  /// Definida no build via --dart-define=API_BASE_URL=...
  static const String urlBasePadrao = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: urlEmulador,
  );

  /// Chave opcional (mesmo valor de FINANCEIRO_API_KEY no servidor local).
  static const String chaveApi = '';

  static bool get conexaoRenderBloqueada =>
      urlBasePadrao.toLowerCase().contains('onrender.com');

  static bool get usaLocalhost =>
      urlBasePadrao.contains('127.0.0.1') || urlBasePadrao.contains('localhost');

  static bool get usaRedeLocal =>
      usaLocalhost ||
      urlBasePadrao.startsWith('http://192.168.') ||
      urlBasePadrao.startsWith('http://10.');

  static String montarUrl(String caminho) {
    _bloquearRender();
    final base = urlBasePadrao.replaceAll(RegExp(r'/+$'), '');
    final path = caminho.startsWith('/') ? caminho : '/$caminho';
    return '$base$path';
  }

  static void _bloquearRender() {
    if (conexaoRenderBloqueada) {
      throw Exception(
        'Conexao com a API Render esta desativada. '
        'Use a API local (executar_api.bat) e gere o APK com mobile\\gerar_apk.bat.',
      );
    }
  }

  static String mensagemErroConexao(Object erro) {
    final detalhe = erro.toString().replaceFirst('Exception: ', '');
    final buffer = StringBuffer()
      ..writeln('Nao foi possivel conectar a API.')
      ..writeln('URL: $urlBasePadrao')
      ..writeln();

    if (conexaoRenderBloqueada) {
      buffer
        ..writeln('A API Render foi desativada neste projeto.')
        ..writeln('Gere um novo APK com mobile\\gerar_apk.bat (API local na Wi-Fi).')
        ..writeln();
    } else if (usaLocalhost) {
      buffer
        ..writeln('Emulador: execute executar_api.bat no PC e use testar_apk.bat.')
        ..writeln();
    } else {
      buffer
        ..writeln('Celular fisico: PC ligado com executar_api.bat na mesma Wi-Fi.')
        ..writeln('Execute liberar_api_rede.bat como administrador (uma vez).')
        ..writeln('Gere o APK com mobile\\gerar_apk.bat para embutir o IP do PC.')
        ..writeln();
    }

    buffer.write(detalhe);
    return buffer.toString();
  }
}
