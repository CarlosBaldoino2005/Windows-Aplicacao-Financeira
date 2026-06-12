import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'servicos/carteira_local.dart';
import 'servicos/estado_api.dart';
import 'telas/inicio_tela.dart';
import 'tema/cores.dart';
import 'widgets/estado_carregando.dart';

void main() {
  runApp(const FinanceiroApp());
}

class FinanceiroApp extends StatelessWidget {
  const FinanceiroApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Financeiro',
      debugShowCheckedModeBanner: false,
      theme: CoresApp.temaClaro(),
      locale: const Locale('pt', 'BR'),
      supportedLocales: const [Locale('pt', 'BR')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: const SplashTela(),
    );
  }
}

class SplashTela extends StatefulWidget {
  const SplashTela({super.key});

  @override
  State<SplashTela> createState() => _SplashTelaState();
}

class _SplashTelaState extends State<SplashTela> {
  @override
  void initState() {
    super.initState();
    _iniciar();
  }

  Future<void> _iniciar() async {
    // Nao bloqueia o app sem internet — verifica provedores em paralelo ao splash.
    final resultados = await Future.wait([
      EstadoApi.atualizarConexao(),
      Future<void>.delayed(const Duration(milliseconds: 500)),
    ]);

    final conectado = resultados.first as bool;
    var indiceInicial = 0;

    if (!conectado) {
      final posicoes = await CarteiraLocal().listar();
      if (posicoes.isNotEmpty) {
        indiceInicial = 3; // aba Carteira
      }
    }

    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => InicioTela(indiceInicial: indiceInicial),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: EstadoCarregando(mensagem: 'Abrindo Financeiro...'),
      ),
    );
  }
}
