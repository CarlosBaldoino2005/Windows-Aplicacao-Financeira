import 'package:intl/intl.dart';

String formatarMoeda(double valor, String moeda) {
  if (moeda == 'BRL') {
    final formato = NumberFormat.currency(locale: 'pt_BR', symbol: 'R\$');
    return formato.format(valor);
  }
  final formato = NumberFormat.currency(locale: 'en_US', symbol: 'US\$');
  return formato.format(valor);
}

String formatarVariacao(double percentual) {
  final sinal = percentual >= 0 ? '+' : '';
  return '$sinal${percentual.toStringAsFixed(2)}%';
}
