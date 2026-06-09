import 'package:flutter/material.dart';

import 'busca_tela.dart';
import 'carteira_tela.dart';
import 'favoritos_tela.dart';
import 'painel_tela.dart';

class InicioTela extends StatefulWidget {
  const InicioTela({super.key});

  @override
  State<InicioTela> createState() => _InicioTelaState();
}

class _InicioTelaState extends State<InicioTela> {
  int _indice = 0;

  final _chavePainel = GlobalKey<PainelTelaState>();
  final _chaveFavoritos = GlobalKey<FavoritosTelaState>();
  final _chaveCarteira = GlobalKey<CarteiraTelaState>();

  void _atualizarTudo() {
    _chavePainel.currentState?.recarregar();
    _chaveFavoritos.currentState?.recarregar();
    _chaveCarteira.currentState?.recarregar();
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final telas = [
      PainelTela(key: _chavePainel),
      const BuscaTela(),
      FavoritosTela(key: _chaveFavoritos),
      CarteiraTela(key: _chaveCarteira),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Financeiro'),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: _atualizarTudo,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: IndexedStack(
        index: _indice,
        children: telas,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _indice,
        onDestinationSelected: (valor) => setState(() => _indice = valor),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.trending_up), label: 'Painel'),
          NavigationDestination(icon: Icon(Icons.search), label: 'Buscar'),
          NavigationDestination(icon: Icon(Icons.star), label: 'Favoritos'),
          NavigationDestination(icon: Icon(Icons.account_balance_wallet), label: 'Carteira'),
        ],
      ),
    );
  }
}
