import 'package:flutter/material.dart';

import '../modelos/cotacao_resumo.dart';
import '../modelos/tipo_ativo.dart';
import '../servicos/api_cliente.dart';
import '../servicos/favoritos_local.dart';
import '../widgets/cotacao_card.dart';
import '../widgets/estado_carregando.dart';
import '../widgets/estado_erro.dart';
import 'grafico_tela.dart';

class FavoritosTela extends StatefulWidget {
  const FavoritosTela({super.key});

  @override
  State<FavoritosTela> createState() => FavoritosTelaState();
}

class FavoritosTelaState extends State<FavoritosTela> {
  final ApiCliente _api = ApiCliente();
  final FavoritosLocal _favoritos = FavoritosLocal();

  bool _carregando = true;
  String? _erro;
  List<({CotacaoResumo cotacao, TipoAtivo tipo})> _itens = [];

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  Future<void> recarregar() => _carregar();

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final favoritos = await _favoritos.listar();
      if (favoritos.isEmpty) {
        setState(() {
          _itens = [];
          _carregando = false;
        });
        return;
      }

      final lista = <({CotacaoResumo cotacao, TipoAtivo tipo})>[];
      for (final fav in favoritos) {
        try {
          final cotacao = await _api.obterCotacao(fav.simbolo, tipo: fav.tipo);
          lista.add((cotacao: cotacao, tipo: fav.tipo));
        } catch (_) {
          // Ignora ticker que falhou e continua os demais.
        }
      }
      if (!mounted) return;
      setState(() {
        _itens = lista;
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

  Future<void> _remover(CotacaoResumo cotacao, TipoAtivo tipo) async {
    await _favoritos.remover(tipo, cotacao.simbolo);
    await _carregar();
  }

  void _abrirGrafico(CotacaoResumo cotacao, TipoAtivo tipo) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => GraficoTela(
          simbolo: cotacao.simbolo,
          codigo: cotacao.codigo,
          tipo: tipo,
          cotacao: cotacao,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_carregando) return const EstadoCarregando(mensagem: 'Carregando favoritos...');
    if (_erro != null) return EstadoErro(mensagem: _erro!, aoTentarNovamente: _carregar);
    if (_itens.isEmpty) {
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
        itemCount: _itens.length,
        itemBuilder: (context, indice) {
          final par = _itens[indice];
          return CotacaoCard(
            cotacao: par.cotacao,
            ehFavorito: true,
            aoAlternarFavorito: () => _remover(par.cotacao, par.tipo),
            aoTocar: () => _abrirGrafico(par.cotacao, par.tipo),
          );
        },
      ),
    );
  }
}
