import '../config/api_config.dart';
import 'api_cliente.dart';

/// Estado global da conexao com os provedores de mercado (Yahoo/Brapi).
class EstadoApi {
  EstadoApi._();

  static bool online = false;
  static String? ultimoErro;

  static const Duration tempoLimitePadrao = Duration(seconds: 8);

  /// Tenta consultar os provedores e atualiza [online].
  static Future<bool> atualizarConexao({
    Duration tempoLimite = tempoLimitePadrao,
  }) async {
    try {
      await ApiCliente().verificarSaude().timeout(tempoLimite);
      online = true;
      ultimoErro = null;
      return true;
    } catch (erro) {
      online = false;
      ultimoErro = ApiConfig.mensagemModoOffline();
      return false;
    }
  }

  /// Texto curto para banner quando nao ha internet ou os provedores falham.
  static String mensagemBannerOffline() {
    if (online) return '';
    return ultimoErro ?? ApiConfig.mensagemModoOffline();
  }
}
