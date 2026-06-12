import 'package:flutter/material.dart';

import '../modelos/cotacao_resumo.dart';
import '../modelos/tipo_ativo.dart';
import '../config/api_config.dart';
import '../servicos/api_cliente.dart';
import '../servicos/estado_api.dart';
import '../servicos/favoritos_local.dart';
import '../widgets/cotacao_card.dart';
import '../widgets/estado_carregando.dart';
import '../widgets/estado_erro.dart';
import '../widgets/seletor_tipo_ativo.dart';
import 'grafico_tela.dart';

class PainelTela extends StatefulWidget {
  const PainelTela({super.key});

  @override
  State<PainelTela> createState() => PainelTelaState();
}

class PainelTelaState extends State<PainelTela> with SingleTickerProviderStateMixin {
  final ApiCliente _api = ApiCliente();
  final FavoritosLocal _servicoFavoritos = FavoritosLocal();

  late TabController _abas;
  TipoAtivo _tipo = TipoAtivo.acoes;
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

  /// Chamado pelo botão Atualizar da tela principal.
  Future<void> recarregar() => _carregar();

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    if (!EstadoApi.online) {
      setState(() {
        _erro = ApiConfig.mensagemModoOffline();
        _carregando = false;
      });
      return;
    }

    try {
      final painel = await _api.obterPainel(tipo: _tipo);
      final fav = await _servicoFavoritos.listar();
      if (!mounted) return;
      setState(() {
        _emAlta = painel['emAlta'] ?? [];
        _emQueda = painel['emQueda'] ?? [];
        _todas = painel['todas'] ?? [];
        _favoritosSimbolos = fav
            .where((item) => item.tipo == _tipo)
            .map((item) => item.simbolo)
            .toSet();
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

  void _mudarTipo(TipoAtivo novo) {
    if (novo == _tipo) return;
    setState(() => _tipo = novo);
    _carregar();
  }

  Future<void> _alternarFavorito(CotacaoResumo cotacao) async {
    final simbolo = cotacao.simbolo;
    try {
      if (_favoritosSimbolos.contains(simbolo)) {
        await _servicoFavoritos.remover(_tipo, simbolo);
        setState(() => _favoritosSimbolos.remove(simbolo));
      } else {
        await _servicoFavoritos.adicionar(_tipo, simbolo);
        setState(() => _favoritosSimbolos.add(simbolo));
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  void _abrirGrafico(CotacaoResumo cotacao) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => GraficoTela(
          simbolo: cotacao.simbolo,
          codigo: cotacao.codigo,
          tipo: _tipo,
          cotacao: cotacao,
        ),
      ),
    );
  }

  Widget _lista(List<CotacaoResumo> itens) {
    if (itens.isEmpty) {
      return Center(child: Text('Nenhum ativo nesta aba (${_tipo.rotulo}).'));
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
            aoTocar: () => _abrirGrafico(item),
          );
        },
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
        if (_carregando)
          const Expanded(child: EstadoCarregando(mensagem: 'Carregando painel...'))
        else if (_erro != null)
          Expanded(child: EstadoErro(mensagem: _erro!, aoTentarNovamente: _carregar))
        else ...[
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
      ],
    );
  }
}
