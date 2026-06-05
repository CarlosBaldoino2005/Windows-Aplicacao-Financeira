import 'package:flutter/material.dart';

import 'busca_tela.dart';
import 'favoritos_tela.dart';
import 'painel_tela.dart';

class InicioTela extends StatefulWidget {
  const InicioTela({super.key});

  @override
  State<InicioTela> createState() => _InicioTelaState();
}

class _InicioTelaState extends State<InicioTela> {
  int _indice = 0;

  final _telas = const [
    PainelTela(),
    BuscaTela(),
    FavoritosTela(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Financeiro'),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: () => setState(() {}),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: IndexedStack(
        index: _indice,
        children: _telas,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _indice,
        onDestinationSelected: (valor) => setState(() => _indice = valor),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.trending_up), label: 'Painel'),
          NavigationDestination(icon: Icon(Icons.search), label: 'Buscar'),
          NavigationDestination(icon: Icon(Icons.star), label: 'Favoritos'),
        ],
      ),
    );
  }
}
