import 'package:shared_preferences/shared_preferences.dart';

/// Parâmetros da carteira (ex.: variação para monitoramento).
class CarteiraConfig {
  static const String _chaveVariacaoPct = 'carteira_variacao_monitoramento_pct';
  static const double variacaoPadraoPct = 10.0;

  Future<double> obterVariacaoMonitoramentoPct() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getDouble(_chaveVariacaoPct) ?? variacaoPadraoPct;
  }

  Future<void> salvarVariacaoMonitoramentoPct(double valor) async {
    final pct = valor.clamp(1.0, 50.0);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(_chaveVariacaoPct, pct);
  }
}
