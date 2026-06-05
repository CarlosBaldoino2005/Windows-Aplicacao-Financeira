import 'package:shared_preferences/shared_preferences.dart';

import '../modelos/tipo_ativo.dart';

/// Favorito com tipo de ativo e simbolo.
class FavoritoItem {
  FavoritoItem({required this.tipo, required this.simbolo});

  final TipoAtivo tipo;
  final String simbolo;

  String get chaveArmazenamento => '${tipo.chave}:$simbolo';

  static FavoritoItem? fromChaveArmazenamento(String valor) {
    final partes = valor.split(':');
    if (partes.length < 2) {
      return FavoritoItem(tipo: TipoAtivo.acoes, simbolo: valor.trim().toUpperCase());
    }
    final tipo = TipoAtivo.fromChave(partes.first);
    final simbolo = partes.sublist(1).join(':').trim().toUpperCase();
    if (simbolo.isEmpty) return null;
    return FavoritoItem(tipo: tipo, simbolo: simbolo);
  }
}

/// Favoritos salvos no celular (ate 40 tickers).
class FavoritosLocal {
  static const String _chave = 'favoritos_acoes';
  static const int limite = 40;

  Future<List<FavoritoItem>> listar() async {
    final prefs = await SharedPreferences.getInstance();
    final bruto = prefs.getStringList(_chave) ?? [];
    final itens = <FavoritoItem>[];
    for (final linha in bruto) {
      final item = FavoritoItem.fromChaveArmazenamento(linha);
      if (item != null) itens.add(item);
    }
    return itens;
  }

  Future<bool> adicionar(TipoAtivo tipo, String simbolo) async {
    final codigo = simbolo.trim().toUpperCase();
    if (codigo.isEmpty) return false;

    final prefs = await SharedPreferences.getInstance();
    final bruto = prefs.getStringList(_chave) ?? [];
    final item = FavoritoItem(tipo: tipo, simbolo: codigo);
    final chave = item.chaveArmazenamento;

    if (bruto.contains(chave)) return true;
    if (bruto.length >= limite) {
      throw Exception('Limite de $limite favoritos atingido.');
    }
    bruto.insert(0, chave);
    await prefs.setStringList(_chave, bruto);
    return true;
  }

  Future<void> remover(TipoAtivo tipo, String simbolo) async {
    final prefs = await SharedPreferences.getInstance();
    final bruto = prefs.getStringList(_chave) ?? [];
    final chave = FavoritoItem(tipo: tipo, simbolo: simbolo.trim().toUpperCase()).chaveArmazenamento;
    bruto.remove(chave);
    bruto.remove(simbolo.trim().toUpperCase());
    await prefs.setStringList(_chave, bruto);
  }

  Future<bool> contem(TipoAtivo tipo, String simbolo) async {
    final lista = await listar();
    final codigo = simbolo.trim().toUpperCase();
    return lista.any((item) => item.tipo == tipo && item.simbolo == codigo);
  }
}
