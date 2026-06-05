import 'package:shared_preferences/shared_preferences.dart';

/// Favoritos salvos no celular (ate 40 tickers).
class FavoritosLocal {
  static const String _chave = 'favoritos_acoes';
  static const int limite = 40;

  Future<List<String>> listar() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_chave) ?? [];
  }

  Future<bool> adicionar(String simbolo) async {
    final codigo = simbolo.trim().toUpperCase();
    if (codigo.isEmpty) return false;

    final prefs = await SharedPreferences.getInstance();
    final lista = prefs.getStringList(_chave) ?? [];
    if (lista.contains(codigo)) return true;
    if (lista.length >= limite) {
      throw Exception('Limite de $limite favoritos atingido.');
    }
    lista.insert(0, codigo);
    await prefs.setStringList(_chave, lista);
    return true;
  }

  Future<void> remover(String simbolo) async {
    final prefs = await SharedPreferences.getInstance();
    final lista = prefs.getStringList(_chave) ?? [];
    lista.remove(simbolo.trim().toUpperCase());
    await prefs.setStringList(_chave, lista);
  }
}
