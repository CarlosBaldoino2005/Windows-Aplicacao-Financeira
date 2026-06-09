/// Cálculos de dividendos para posições da carteira.
class DividendosCarteiraHelper {
  static DateTime? parseData(String texto) {
    final limpo = texto.trim().split(' ').first;
    final partes = limpo.split('/');
    if (partes.length == 3) {
      final dia = int.tryParse(partes[0]);
      final mes = int.tryParse(partes[1]);
      final ano = int.tryParse(partes[2]);
      if (dia != null && mes != null && ano != null) {
        try {
          return DateTime(ano, mes, dia);
        } catch (_) {
          return null;
        }
      }
    }
    if (limpo.contains('-')) {
      return DateTime.tryParse(limpo);
    }
    return null;
  }

  /// Soma dividendos pagos desde a data de compra até hoje.
  static double calcularRecebidos({
    required List<Map<String, dynamic>> pagamentos,
    required String dataCompraTexto,
    required double quantidade,
    DateTime? referencia,
  }) {
    final compra = parseData(dataCompraTexto);
    if (compra == null || quantidade <= 0) return 0;

    final hoje = referencia ?? DateTime.now();
    var total = 0.0;

    for (final item in pagamentos) {
      final dataTexto =
          item['dataPagamento']?.toString() ?? item['dataIso']?.toString() ?? '';
      final data = parseData(dataTexto);
      if (data == null) continue;
      if (data.isBefore(DateTime(compra.year, compra.month, compra.day))) {
        continue;
      }
      if (data.isAfter(hoje)) continue;

      final valorCota = (item['valorPorCota'] as num?)?.toDouble();
      if (valorCota == null || valorCota <= 0) continue;
      total += valorCota * quantidade;
    }

    return total;
  }

  /// Estima próximo pagamento com base no histórico (intervalo médio + último valor).
  static ({
    String data,
    double? valorPorCota,
    double? valorPrevistoTotal,
  }) estimarProximo({
    required List<Map<String, dynamic>> pagamentos,
    required double quantidade,
    DateTime? referencia,
  }) {
    final hoje = referencia ?? DateTime.now();
    final datas = <DateTime>[];
    final valores = <double>[];

    for (final item in pagamentos) {
      final dataTexto =
          item['dataPagamento']?.toString() ?? item['dataIso']?.toString() ?? '';
      final data = parseData(dataTexto);
      final valor = (item['valorPorCota'] as num?)?.toDouble();
      if (data == null || valor == null || valor <= 0) continue;
      datas.add(data);
      valores.add(valor);
    }

    if (datas.isEmpty) {
      return (data: '', valorPorCota: null, valorPrevistoTotal: null);
    }

    final pares = List.generate(datas.length, (i) => (datas[i], valores[i]))
      ..sort((a, b) => b.$1.compareTo(a.$1));

    for (final par in pares) {
      if (par.$1.isAfter(hoje)) {
        final previsto = par.$2 * quantidade;
        return (
          data: _formatarData(par.$1),
          valorPorCota: par.$2,
          valorPrevistoTotal: previsto,
        );
      }
    }

    final ultimo = pares.first;
    var intervaloDias = 90;
    if (pares.length >= 2) {
      final difs = <int>[];
      for (var i = 0; i < pares.length - 1 && i < 4; i++) {
        difs.add(pares[i].$1.difference(pares[i + 1].$1).inDays.abs());
      }
      if (difs.isNotEmpty) {
        intervaloDias = (difs.reduce((a, b) => a + b) / difs.length).round();
        if (intervaloDias < 30) intervaloDias = 30;
      }
    }

    final proxima = ultimo.$1.add(Duration(days: intervaloDias));
    final valorCota = ultimo.$2;
    return (
      data: _formatarData(proxima),
      valorPorCota: valorCota,
      valorPrevistoTotal: valorCota * quantidade,
    );
  }

  static String _formatarData(DateTime data) {
    final d = data.day.toString().padLeft(2, '0');
    final m = data.month.toString().padLeft(2, '0');
    return '$d/$m/${data.year}';
  }
}
