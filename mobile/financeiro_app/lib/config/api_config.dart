/// Configuracoes legadas e mensagens de conexao do app mobile.
class ApiConfig {
  /// Mantido para compatibilidade com builds antigos; nao e mais usado para cotacoes.
  static const String urlEmulador = 'http://127.0.0.1:8000';

  static const String urlBasePadrao = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: urlEmulador,
  );

  static const String chaveApi = '';

  static bool get conexaoRenderBloqueada =>
      urlBasePadrao.toLowerCase().contains('onrender.com');

  /// Mensagem amigavel quando nao ha internet ou os provedores falham.
  static String mensagemModoOffline() {
    return 'Modo offline. Verifique sua conexao com a internet para cotacoes, '
        'graficos e busca. A carteira local continua disponivel.';
  }

  static String mensagemErroConexao(Object erro) {
    final detalhe = erro.toString().replaceFirst('Exception: ', '');
    final buffer = StringBuffer()
      ..writeln(mensagemModoOffline())
      ..writeln();

    if (!detalhe.contains('Modo offline') && detalhe.isNotEmpty) {
      buffer.write(detalhe);
    }
    return buffer.toString();
  }
}
