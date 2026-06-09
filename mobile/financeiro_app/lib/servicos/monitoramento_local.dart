import 'dart:convert';
import 'dart:math';

import 'package:shared_preferences/shared_preferences.dart';

import '../modelos/item_monitoramento.dart';
import '../modelos/tipo_ativo.dart';

/// Monitoramento de preços salvo no celular (limites alto/baixo).
class MonitoramentoLocal {
  static const String _chave = 'monitoramento_itens';
  static const int limite = 100;

  Future<List<ItemMonitoramento>> listar() async {
    final prefs = await SharedPreferences.getInstance();
    final bruto = prefs.getString(_chave);
    if (bruto == null || bruto.isEmpty) return [];

    final json = jsonDecode(bruto) as Map<String, dynamic>;
    final lista = json['itens'] as List<dynamic>? ?? [];
    return lista
        .map((e) => ItemMonitoramento.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
  }

  Future<void> _salvar(List<ItemMonitoramento> itens) async {
    final prefs = await SharedPreferences.getInstance();
    final payload = jsonEncode({
      'itens': itens.map((e) => e.paraJson()).toList(),
    });
    await prefs.setString(_chave, payload);
  }

  String _novoId() =>
      '${DateTime.now().millisecondsSinceEpoch}${Random().nextInt(9999)}';

  /// Cadastra ou atualiza limites para o ativo (usado pela carteira).
  Future<void> sincronizarLimites({
    required TipoAtivo tipo,
    required String simbolo,
    required double precoReferencia,
    required double variacaoPct,
  }) async {
    final codigo = simbolo.trim().toUpperCase();
    if (codigo.isEmpty || precoReferencia <= 0) return;

    final fator = variacaoPct / 100;
    final valorBaixo = precoReferencia * (1 - fator);
    final valorAlto = precoReferencia * (1 + fator);

    final itens = await listar();
    final indice = itens.indexWhere(
      (item) => item.tipo == tipo && item.simbolo == codigo,
    );

    if (indice >= 0) {
      final atual = itens[indice];
      itens[indice] = ItemMonitoramento(
        id: atual.id,
        tipo: tipo,
        simbolo: codigo,
        valorBaixo: valorBaixo,
        valorAlto: valorAlto,
        pausado: false,
      );
    } else {
      if (itens.length >= limite) {
        throw Exception('Limite de $limite itens em monitoramento.');
      }
      itens.add(ItemMonitoramento(
        id: _novoId(),
        tipo: tipo,
        simbolo: codigo,
        valorBaixo: valorBaixo,
        valorAlto: valorAlto,
      ));
    }

    await _salvar(itens);
  }

  Future<void> remover(TipoAtivo tipo, String simbolo) async {
    final codigo = simbolo.trim().toUpperCase();
    final itens = await listar();
    itens.removeWhere((item) => item.tipo == tipo && item.simbolo == codigo);
    await _salvar(itens);
  }
}
