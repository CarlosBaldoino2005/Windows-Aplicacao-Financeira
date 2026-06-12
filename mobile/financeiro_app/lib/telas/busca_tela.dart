import 'package:flutter/material.dart';

import '../modelos/resultado_busca.dart';
import '../modelos/tipo_ativo.dart';
import '../config/api_config.dart';
import '../servicos/api_cliente.dart';
import '../servicos/estado_api.dart';
import '../servicos/favoritos_local.dart';
import '../tema/cores.dart';
import '../widgets/estado_carregando.dart';
import '../widgets/seletor_tipo_ativo.dart';
import 'grafico_tela.dart';

class BuscaTela extends StatefulWidget {
  const BuscaTela({super.key});

  @override
  State<BuscaTela> createState() => BuscaTelaState();
}

class BuscaTelaState extends State<BuscaTela> {
  final ApiCliente _api = ApiCliente();
  final FavoritosLocal _servicoFavoritos = FavoritosLocal();
  final TextEditingController _campo = TextEditingController();

  TipoAtivo _tipo = TipoAtivo.acoes;
  bool _carregando = false;
  String? _erro;
  List<ResultadoBusca> _resultados = [];
  Set<String> _favoritosSimbolos = {};

  @override
  void initState() {
    super.initState();
    _carregarFavoritos();
  }

  @override
  void dispose() {
    _campo.dispose();
    super.dispose();
  }

  String get _dicaCampo {
    return switch (_tipo) {
      TipoAtivo.cripto => 'BTC, ETH, SOL...',
      TipoAtivo.fiis => 'HGLG11, MXRF11...',
      TipoAtivo.indices => 'Use o painel Índices',
      TipoAtivo.acoes => 'PETR4, Vale, AAPL...',
    };
  }

  Future<void> _carregarFavoritos() async {
    final lista = await _servicoFavoritos.listar();
    if (mounted) {
      setState(() {
        _favoritosSimbolos = lista
            .where((item) => item.tipo == _tipo)
            .map((item) => item.simbolo)
            .toSet();
      });
    }
  }

  void _mudarTipo(TipoAtivo novo) {
    setState(() {
      _tipo = novo;
      _resultados = [];
      _erro = null;
    });
    _carregarFavoritos();
  }

  Future<void> _pesquisar() async {
    if (!EstadoApi.online) {
      setState(() {
        _erro = ApiConfig.mensagemModoOffline();
        _resultados = [];
      });
      return;
    }

    if (_tipo == TipoAtivo.indices) {
      setState(() {
        _erro = 'Para índices, use a aba Painel → Índices.';
        _resultados = [];
      });
      return;
    }

    final termo = _campo.text.trim();
    if (termo.length < 2) {
      setState(() {
        _erro = 'Digite ao menos 2 caracteres.';
        _resultados = [];
      });
      return;
    }

    setState(() {
      _carregando = true;
      _erro = null;
    });

    try {
      final lista = await _api.buscar(termo, tipo: _tipo);
      if (!mounted) return;
      setState(() {
        _resultados = lista;
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

  Future<void> _alternarFavorito(ResultadoBusca item) async {
    try {
      if (_favoritosSimbolos.contains(item.simbolo)) {
        await _servicoFavoritos.remover(_tipo, item.simbolo);
        setState(() => _favoritosSimbolos.remove(item.simbolo));
      } else {
        await _servicoFavoritos.adicionar(_tipo, item.simbolo);
        setState(() => _favoritosSimbolos.add(item.simbolo));
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  void _abrirAtivo(ResultadoBusca item) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => GraficoTela(
          simbolo: item.simbolo,
          codigo: item.codigo,
          tipo: _tipo,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SeletorTipoAtivo(
          tipoSelecionado: _tipo,
          aoMudar: _mudarTipo,
        ),
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _campo,
                  decoration: InputDecoration(
                    hintText: _dicaCampo,
                    border: const OutlineInputBorder(),
                    isDense: true,
                  ),
                  textInputAction: TextInputAction.search,
                  onSubmitted: (_) => _pesquisar(),
                ),
              ),
              const SizedBox(width: 8),
              FilledButton(
                onPressed: _pesquisar,
                child: const Text('Buscar'),
              ),
            ],
          ),
        ),
        if (_carregando) const Expanded(child: EstadoCarregando()),
        if (!_carregando && _erro != null)
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(_erro!, style: const TextStyle(color: CoresApp.erro)),
          ),
        if (!_carregando && _erro == null)
          Expanded(
            child: ListView.builder(
              itemCount: _resultados.length,
              itemBuilder: (context, indice) {
                final item = _resultados[indice];
                final fav = _favoritosSimbolos.contains(item.simbolo);
                return ListTile(
                  title: Text(item.codigo, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('${item.nome} • ${item.bolsa}'),
                  onTap: () => _abrirAtivo(item),
                  trailing: IconButton(
                    icon: Icon(
                      fav ? Icons.star : Icons.star_border,
                      color: fav ? Colors.amber : null,
                    ),
                    onPressed: () => _alternarFavorito(item),
                  ),
                );
              },
            ),
          ),
      ],
    );
  }
}
