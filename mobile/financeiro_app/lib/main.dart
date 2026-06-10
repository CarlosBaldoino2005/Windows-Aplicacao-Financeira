import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'config/api_config.dart';
import 'servicos/api_cliente.dart';
import 'telas/inicio_tela.dart';
import 'tema/cores.dart';
import 'widgets/estado_carregando.dart';
import 'widgets/estado_erro.dart';

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
  final ApiCliente _api = ApiCliente();
  bool _carregando = true;
  String? _erro;

  @override
  void initState() {
    super.initState();
    _verificarApi();
  }

  Future<void> _verificarApi() async {
    try {
      await _api.verificarSaude();
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const InicioTela()),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _erro = ApiConfig.mensagemErroConexao(e);
        _carregando = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: _carregando
            ? const EstadoCarregando(mensagem: 'Conectando a API...')
            : EstadoErro(mensagem: _erro!, aoTentarNovamente: () {
                setState(() {
                  _carregando = true;
                  _erro = null;
                });
                _verificarApi();
              }),
      ),
    );
  }
}
