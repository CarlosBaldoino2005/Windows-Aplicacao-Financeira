import 'package:flutter/material.dart';

import '../modelos/cotacao_resumo.dart';
import '../servicos/api_cliente.dart';
import '../servicos/favoritos_local.dart';
import '../widgets/cotacao_card.dart';
import '../widgets/estado_carregando.dart';
import '../widgets/estado_erro.dart';

class FavoritosTela extends StatefulWidget {
  const FavoritosTela({super.key});

  @override
  State<FavoritosTela> createState() => _FavoritosTelaState();
}

class _FavoritosTelaState extends State<FavoritosTela> {
  final ApiCliente _api = ApiCliente();
  final FavoritosLocal _favoritos = FavoritosLocal();

  bool _carregando = true;
  String? _erro;
  List<CotacaoResumo> _cotacoes = [];

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final simbolos = await _favoritos.listar();
      if (simbolos.isEmpty) {
        setState(() {
          _cotacoes = [];
          _carregando = false;
        });
        return;
      }

      final lista = <CotacaoResumo>[];
      for (final simbolo in simbolos) {
        try {
          lista.add(await _api.obterCotacao(simbolo));
        } catch (_) {
          // Ignora ticker que falhou e continua os demais.
        }
      }
      if (!mounted) return;
      setState(() {
        _cotacoes = lista;
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

  Future<void> _remover(CotacaoResumo cotacao) async {
    await _favoritos.remover(cotacao.simbolo);
    await _carregar();
  }

  @override
  Widget build(BuildContext context) {
    if (_carregando) return const EstadoCarregando(mensagem: 'Carregando favoritos...');
    if (_erro != null) return EstadoErro(mensagem: _erro!, aoTentarNovamente: _carregar);
    if (_cotacoes.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'Nenhum favorito ainda. Use a estrela no painel ou na busca.',
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _carregar,
      child: ListView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        itemCount: _cotacoes.length,
        itemBuilder: (context, indice) {
          final item = _cotacoes[indice];
          return CotacaoCard(
            cotacao: item,
            ehFavorito: true,
            aoAlternarFavorito: () => _remover(item),
          );
        },
      ),
    );
  }
}
