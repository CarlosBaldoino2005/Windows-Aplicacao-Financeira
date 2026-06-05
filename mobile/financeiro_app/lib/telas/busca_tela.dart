import 'package:flutter/material.dart';

import '../modelos/resultado_busca.dart';
import '../servicos/api_cliente.dart';
import '../servicos/favoritos_local.dart';
import '../tema/cores.dart';
import '../widgets/estado_carregando.dart';

class BuscaTela extends StatefulWidget {
  const BuscaTela({super.key});

  @override
  State<BuscaTela> createState() => _BuscaTelaState();
}

class _BuscaTelaState extends State<BuscaTela> {
  final ApiCliente _api = ApiCliente();
  final FavoritosLocal _favoritos = FavoritosLocal();
  final TextEditingController _campo = TextEditingController();

  bool _carregando = false;
  String? _erro;
  List<ResultadoBusca> _resultados = [];
  Set<String> _favoritos = {};

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

  Future<void> _carregarFavoritos() async {
    final lista = await _favoritos.listar();
    if (mounted) setState(() => _favoritos = lista.toSet());
  }

  Future<void> _pesquisar() async {
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
      final lista = await _api.buscarAcoes(termo);
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
      if (_favoritos.contains(item.simbolo)) {
        await _favoritos.remover(item.simbolo);
        setState(() => _favoritos.remove(item.simbolo));
      } else {
        await _favoritos.adicionar(item.simbolo);
        setState(() => _favoritos.add(item.simbolo));
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _campo,
                  decoration: const InputDecoration(
                    hintText: 'PETR4, Vale, AAPL...',
                    border: OutlineInputBorder(),
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
                final fav = _favoritos.contains(item.simbolo);
                return ListTile(
                  title: Text(item.codigo, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('${item.nome} • ${item.bolsa}'),
                  trailing: IconButton(
                    icon: Icon(fav ? Icons.star : Icons.star_border, color: fav ? Colors.amber : null),
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
