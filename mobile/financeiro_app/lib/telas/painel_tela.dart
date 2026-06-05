import 'package:flutter/material.dart';

import '../modelos/cotacao_resumo.dart';
import '../servicos/api_cliente.dart';
import '../servicos/favoritos_local.dart';
import '../widgets/cotacao_card.dart';
import '../widgets/estado_carregando.dart';
import '../widgets/estado_erro.dart';

class PainelTela extends StatefulWidget {
  const PainelTela({super.key});

  @override
  State<PainelTela> createState() => _PainelTelaState();
}

class _PainelTelaState extends State<PainelTela> with SingleTickerProviderStateMixin {
  final ApiCliente _api = ApiCliente();
  final FavoritosLocal _servicoFavoritos = FavoritosLocal();

  late TabController _abas;
  bool _carregando = true;
  String? _erro;
  List<CotacaoResumo> _emAlta = [];
  List<CotacaoResumo> _emQueda = [];
  List<CotacaoResumo> _todas = [];
  Set<String> _favoritosSimbolos = {};

  @override
  void initState() {
    super.initState();
    _abas = TabController(length: 3, vsync: this);
    _carregar();
  }

  @override
  void dispose() {
    _abas.dispose();
    super.dispose();
  }

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final painel = await _api.obterPainel();
      final fav = await _servicoFavoritos.listar();
      if (!mounted) return;
      setState(() {
        _emAlta = painel['emAlta'] ?? [];
        _emQueda = painel['emQueda'] ?? [];
        _todas = painel['todas'] ?? [];
        _favoritosSimbolos = fav.toSet();
        _carregando = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _erro = e.toString().replaceFirst('Exception: ', '');
        _carregando = false;
      });
    }
  }

  Future<void> _alternarFavorito(CotacaoResumo cotacao) async {
    final simbolo = cotacao.simbolo;
    try {
      if (_favoritosSimbolos.contains(simbolo)) {
        await _servicoFavoritos.remover(simbolo);
        setState(() => _favoritosSimbolos.remove(simbolo));
      } else {
        await _servicoFavoritos.adicionar(simbolo);
        setState(() => _favoritosSimbolos.add(simbolo));
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  Widget _lista(List<CotacaoResumo> itens) {
    if (itens.isEmpty) {
      return const Center(child: Text('Nenhuma acao nesta aba.'));
    }
    return RefreshIndicator(
      onRefresh: _carregar,
      child: ListView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        itemCount: itens.length,
        itemBuilder: (context, indice) {
          final item = itens[indice];
          return CotacaoCard(
            cotacao: item,
            ehFavorito: _favoritosSimbolos.contains(item.simbolo),
            aoAlternarFavorito: () => _alternarFavorito(item),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_carregando) return const EstadoCarregando(mensagem: 'Carregando painel...');
    if (_erro != null) {
      return EstadoErro(mensagem: _erro!, aoTentarNovamente: _carregar);
    }

    return Column(
      children: [
        Material(
          color: Theme.of(context).cardColor,
          child: TabBar(
            controller: _abas,
            tabs: const [
              Tab(text: 'Em alta'),
              Tab(text: 'Em queda'),
              Tab(text: 'Todas'),
            ],
          ),
        ),
        Expanded(
          child: TabBarView(
            controller: _abas,
            children: [
              _lista(_emAlta),
              _lista(_emQueda),
              _lista(_todas),
            ],
          ),
        ),
      ],
    );
  }
}
