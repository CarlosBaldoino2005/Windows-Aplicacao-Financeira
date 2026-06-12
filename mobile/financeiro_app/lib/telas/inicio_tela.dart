import 'package:flutter/material.dart';

import '../servicos/estado_api.dart';
import '../tema/cores.dart';
import 'busca_tela.dart';
import 'carteira_tela.dart';
import 'favoritos_tela.dart';
import 'painel_tela.dart';

class InicioTela extends StatefulWidget {
  const InicioTela({super.key, this.indiceInicial = 0});

  final int indiceInicial;

  @override
  State<InicioTela> createState() => _InicioTelaState();
}

class _InicioTelaState extends State<InicioTela> {
  late int _indice;

  final _chavePainel = GlobalKey<PainelTelaState>();
  final _chaveFavoritos = GlobalKey<FavoritosTelaState>();
  final _chaveCarteira = GlobalKey<CarteiraTelaState>();

  @override
  void initState() {
    super.initState();
    _indice = widget.indiceInicial.clamp(0, 3);
  }

  Future<void> _atualizarTudo() async {
    await EstadoApi.atualizarConexao();
    if (!mounted) return;
    setState(() {});
    _chavePainel.currentState?.recarregar();
    _chaveFavoritos.currentState?.recarregar();
    _chaveCarteira.currentState?.recarregar();
  }

  Widget _bannerOffline() {
    if (EstadoApi.online) return const SizedBox.shrink();

    return MaterialBanner(
      backgroundColor: const Color(0xFFFFF7ED),
      content: Text(
        EstadoApi.mensagemBannerOffline(),
        style: const TextStyle(fontSize: 13, color: CoresApp.texto),
      ),
      leading: const Icon(Icons.cloud_off, color: Color(0xFFD97706)),
      actions: [
        TextButton(
          onPressed: _atualizarTudo,
          child: const Text('Atualizar'),
        ),
      ],
    );
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
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _bannerOffline(),
          Expanded(
            child: IndexedStack(
              index: _indice,
              children: telas,
            ),
          ),
        ],
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
