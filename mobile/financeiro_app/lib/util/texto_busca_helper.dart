/// Normalizacao de texto para buscas sem diferenciar maiusculas e acentos.
String normalizarTextoBusca(String texto) {
  if (texto.isEmpty) return '';
  final minusculo = texto.toLowerCase();
  final buffer = StringBuffer();
  for (final rune in minusculo.runes) {
    final caractere = String.fromCharCode(rune);
    const mapaAcentos = {
      'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
      'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
      'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
      'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
      'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
      'ç': 'c', 'ñ': 'n',
    };
    buffer.write(mapaAcentos[caractere] ?? caractere);
  }
  return buffer.toString().trim();
}

bool textoContemBusca(String termo, List<String> textos) {
  final chave = normalizarTextoBusca(termo);
  if (chave.isEmpty) return false;
  for (final texto in textos) {
    if (normalizarTextoBusca(texto).contains(chave)) return true;
  }
  return false;
}
