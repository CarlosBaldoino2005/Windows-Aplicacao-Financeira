import 'dart:convert';
import 'dart:math';

import 'package:shared_preferences/shared_preferences.dart';

import '../modelos/posicao_carteira.dart';
import '../modelos/tipo_ativo.dart';
import 'carteira_config.dart';
import 'monitoramento_local.dart';

/// Persistência local das posições da carteira.
class CarteiraLocal {
  static const String _chave = 'carteira_posicoes';
  static const int limite = 200;

  final MonitoramentoLocal _monitoramento = MonitoramentoLocal();
  final CarteiraConfig _config = CarteiraConfig();

  Future<List<PosicaoCarteira>> listar() async {
    final prefs = await SharedPreferences.getInstance();
    final bruto = prefs.getString(_chave);
    if (bruto == null || bruto.isEmpty) return [];

    final json = jsonDecode(bruto) as Map<String, dynamic>;
    final lista = json['posicoes'] as List<dynamic>? ?? [];
    return lista
        .map((e) => PosicaoCarteira.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
  }

  Future<void> _salvar(List<PosicaoCarteira> posicoes) async {
    final prefs = await SharedPreferences.getInstance();
    final payload = jsonEncode({
      'posicoes': posicoes.map((e) => e.paraJson()).toList(),
    });
    await prefs.setString(_chave, payload);
  }

  String _novoId() =>
      '${DateTime.now().millisecondsSinceEpoch}${Random().nextInt(9999)}';

  Future<PosicaoCarteira> adicionar({
    required TipoAtivo tipo,
    required String simbolo,
    required double quantidade,
    required double precoCompra,
    required String dataCompra,
  }) async {
    final codigo = simbolo.trim().toUpperCase();
    final posicoes = await listar();

    if (posicoes.length >= limite) {
      throw Exception('Limite de $limite posições na carteira.');
    }

    final nova = PosicaoCarteira(
      id: _novoId(),
      tipo: tipo,
      simbolo: codigo,
      quantidade: quantidade,
      precoCompra: precoCompra,
      dataCompra: dataCompra,
    );

    posicoes.insert(0, nova);
    await _salvar(posicoes);
    await _sincronizarMonitoramentoGrupo(tipo, codigo);
    return nova;
  }

  Future<void> atualizar(PosicaoCarteira posicao) async {
    final posicoes = await listar();
    final indice = posicoes.indexWhere((p) => p.id == posicao.id);
    if (indice < 0) {
      throw Exception('Posição não encontrada na carteira.');
    }

    posicoes[indice] = posicao;
    await _salvar(posicoes);
    await _sincronizarMonitoramentoGrupo(posicao.tipo, posicao.simbolo);
  }

  /// Registra venda reduzindo a quantidade (remove se zerar).
  Future<void> registrarVenda({
    required String id,
    required double quantidadeVendida,
  }) async {
    if (quantidadeVendida <= 0) {
      throw Exception('Quantidade de venda inválida.');
    }

    final posicoes = await listar();
    final indice = posicoes.indexWhere((p) => p.id == id);
    if (indice < 0) throw Exception('Posição não encontrada.');

    final atual = posicoes[indice];
    final restante = atual.quantidade - quantidadeVendida;
    if (restante < 0) {
      throw Exception('Quantidade vendida maior que a posição.');
    }

    if (restante == 0) {
      posicoes.removeAt(indice);
    } else {
      posicoes[indice] = atual.copiarCom(quantidade: restante);
    }

    await _salvar(posicoes);
    await _sincronizarMonitoramentoGrupo(atual.tipo, atual.simbolo);
  }

  Future<void> remover(String id) async {
    final posicoes = await listar();
    final indice = posicoes.indexWhere((p) => p.id == id);
    if (indice < 0) return;

    final removida = posicoes.removeAt(indice);
    await _salvar(posicoes);
    await _sincronizarMonitoramentoGrupo(removida.tipo, removida.simbolo);
  }

  Future<void> _sincronizarMonitoramento(
    TipoAtivo tipo,
    String simbolo,
    double precoReferencia,
  ) async {
    final pct = await _config.obterVariacaoMonitoramentoPct();
    await _monitoramento.sincronizarLimites(
      tipo: tipo,
      simbolo: simbolo,
      precoReferencia: precoReferencia,
      variacaoPct: pct,
    );
  }

  Future<void> _sincronizarMonitoramentoGrupo(TipoAtivo tipo, String simbolo) async {
    final posicoes = await listar();
    final grupo = posicoes
        .where((pos) => pos.tipo == tipo && pos.simbolo == simbolo)
        .toList();

    if (grupo.isEmpty) {
      await _monitoramento.remover(tipo, simbolo);
      return;
    }

    var qtdTotal = 0.0;
    var investido = 0.0;
    for (final pos in grupo) {
      qtdTotal += pos.quantidade;
      investido += pos.valorInvestido;
    }
    final precoMedio =
        qtdTotal > 0 ? investido / qtdTotal : grupo.first.precoCompra;
    await _sincronizarMonitoramento(tipo, simbolo, precoMedio);
  }

  /// Reaplica limites de monitoramento após alterar o percentual padrão.
  Future<void> resincronizarMonitoramentoTodas() async {
    final posicoes = await listar();
    final porChave = <String, List<PosicaoCarteira>>{};

    for (final pos in posicoes) {
      final chave = '${pos.tipo.chave}:${pos.simbolo}';
      porChave.putIfAbsent(chave, () => []).add(pos);
    }

    for (final grupo in porChave.values) {
      final primeira = grupo.first;
      var qtdTotal = 0.0;
      var investido = 0.0;
      for (final pos in grupo) {
        qtdTotal += pos.quantidade;
        investido += pos.valorInvestido;
      }
      final precoMedio = qtdTotal > 0 ? investido / qtdTotal : primeira.precoCompra;
      await _sincronizarMonitoramento(primeira.tipo, primeira.simbolo, precoMedio);
    }
  }
}
