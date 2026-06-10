import '../modelos/tipo_ativo.dart';

/// Validações de campos da carteira (pt-BR).
class ValidadoresCarteira {
  static String formatarData(DateTime data) {
    final dia = data.day.toString().padLeft(2, '0');
    final mes = data.month.toString().padLeft(2, '0');
    return '$dia/$mes/${data.year}';
  }

  static String dataHoje() => formatarData(DateTime.now());

  static DateTime? parseData(String valor) {
    final texto = valor.trim();
    if (texto.isEmpty) return null;
    final partes = texto.split('/');
    if (partes.length != 3) return null;
    final dia = int.tryParse(partes[0]);
    final mes = int.tryParse(partes[1]);
    final ano = int.tryParse(partes[2]);
    if (dia == null || mes == null || ano == null) return null;
    try {
      final data = DateTime(ano, mes, dia);
      if (data.day != dia || data.month != mes || data.year != ano) {
        return null;
      }
      return data;
    } catch (_) {
      return null;
    }
  }

  /// Normaliza ticker digitado (ex.: PETR4 → PETR4.SA, BTC → BTC-USD).
  static String normalizarSimbolo(String valor, TipoAtivo tipo) {
    final texto = valor.trim().toUpperCase();
    if (texto.isEmpty) return texto;

    if (tipo == TipoAtivo.cripto) {
      final limpo = texto.replaceAll('/', '-').replaceAll(' ', '');
      if (limpo.contains('-USD') || limpo.contains('-USDT')) return limpo;
      if (RegExp(r'^[A-Z0-9]{2,12}$').hasMatch(limpo)) return '$limpo-USD';
      return limpo;
    }

    if (!texto.contains('.') &&
        RegExp(r'^[A-Z]{4}\d{1,2}$').hasMatch(texto)) {
      return '$texto.SA';
    }
    return texto;
  }

  static String codigoExibicao(String simbolo) {
    return simbolo.replaceAll('.SA', '').replaceAll('-USD', '');
  }
  static String? validarSimbolo(String valor) {
    final texto = valor.trim();
    if (texto.isEmpty) return 'Informe o código do ativo.';
    return null;
  }

  static String? validarQuantidade(String valor) {
    final texto = valor.trim().replaceAll(',', '.');
    if (texto.isEmpty) return 'Informe a quantidade.';
    final numero = double.tryParse(texto);
    if (numero == null || numero <= 0) return 'Quantidade inválida.';
    return null;
  }

  static String? validarPreco(String valor) {
    final texto = _normalizarMoeda(valor);
    if (texto.isEmpty) return 'Informe o preço pago.';
    final numero = double.tryParse(texto);
    if (numero == null || numero <= 0) return 'Preço inválido.';
    return null;
  }

  static double? parseQuantidade(String valor) {
    final texto = valor.trim().replaceAll(',', '.');
    return double.tryParse(texto);
  }

  static double? parsePreco(String valor) {
    return double.tryParse(_normalizarMoeda(valor));
  }

  static String? validarDataCompra(String valor) {
    if (parseData(valor) == null) {
      if (valor.trim().isEmpty) return 'Informe a data da compra.';
      return 'Use o formato dd/mm/aaaa.';
    }
    return null;
  }

  static String _normalizarMoeda(String valor) {
    var texto = valor.trim();
    if (texto.isEmpty) return '';
    texto = texto.replaceAll(RegExp(r'[R$\s]'), '');
    if (texto.contains(',') && texto.contains('.')) {
      texto = texto.replaceAll('.', '').replaceAll(',', '.');
    } else if (texto.contains(',')) {
      texto = texto.replaceAll(',', '.');
    }
    return texto;
  }
}
