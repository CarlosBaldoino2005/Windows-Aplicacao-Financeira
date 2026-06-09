/// URL base da API no celular (nuvem Render — nao depende do PC).
class ApiConfig {
  /// API publicada na nuvem. O celular usa sempre esta URL.
  static const String urlRender =
      'https://windows-aplicacao-financeira.onrender.com';

  /// Apenas builds de emulador (gerar_apk_emulador.bat) sobrescrevem via --dart-define.
  static const String urlBasePadrao = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: urlRender,
  );

  /// Chave opcional (mesmo valor de FINANCEIRO_API_KEY no servidor Render).
  static const String chaveApi = '';

  static String montarUrl(String caminho) {
    final base = urlBasePadrao.replaceAll(RegExp(r'/+$'), '');
    final path = caminho.startsWith('/') ? caminho : '/$caminho';
    return '$base$path';
  }

  static bool get usaApiNuvem => urlBasePadrao.startsWith('https://');

  static String mensagemErroConexao(Object erro) {
    final detalhe = erro.toString().replaceFirst('Exception: ', '');
    final buffer = StringBuffer()
      ..writeln('Nao foi possivel conectar a API na nuvem.')
      ..writeln('URL: $urlBasePadrao')
      ..writeln()
      ..writeln('Verifique Wi-Fi ou dados moveis.')
      ..writeln(
        'No plano gratuito do Render, a primeira conexao pode levar ate 1 minuto.',
      )
      ..writeln()
      ..writeln('Se o erro continuar, gere de novo o APK com mobile\\gerar_apk.bat.')
      ..writeln()
      ..write(detalhe);
    return buffer.toString();
  }
}
