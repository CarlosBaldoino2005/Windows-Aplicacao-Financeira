/// Validações de campos da carteira (pt-BR).
class ValidadoresCarteira {
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
    final texto = valor.trim();
    if (texto.isEmpty) return 'Informe a data da compra.';
    final partes = texto.split('/');
    if (partes.length != 3) return 'Use o formato dd/mm/aaaa.';
    final dia = int.tryParse(partes[0]);
    final mes = int.tryParse(partes[1]);
    final ano = int.tryParse(partes[2]);
    if (dia == null || mes == null || ano == null) return 'Data inválida.';
    if (mes < 1 || mes > 12 || dia < 1 || dia > 31 || ano < 1900) {
      return 'Data inválida.';
    }
    try {
      final data = DateTime(ano, mes, dia);
      if (data.day != dia || data.month != mes || data.year != ano) {
        return 'Data inválida.';
      }
    } catch (_) {
      return 'Data inválida.';
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
