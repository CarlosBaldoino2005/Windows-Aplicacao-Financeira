import 'package:flutter/material.dart';

import '../modelos/linha_carteira.dart';
import '../modelos/posicao_carteira.dart';
import '../modelos/tipo_ativo.dart';
import '../servicos/api_cliente.dart';
import '../servicos/carteira_config.dart';
import '../servicos/carteira_local.dart';
import '../tema/cores.dart';
import '../util/dividendos_carteira_helper.dart';
import '../util/formatadores.dart';
import '../widgets/estado_carregando.dart';
import '../widgets/estado_erro.dart';
import 'carteira_form_tela.dart';
import 'grafico_tela.dart';

class CarteiraTela extends StatefulWidget {
  const CarteiraTela({super.key});

  @override
  State<CarteiraTela> createState() => CarteiraTelaState();
}

class CarteiraTelaState extends State<CarteiraTela> {
  final ApiCliente _api = ApiCliente();
  final CarteiraLocal _carteira = CarteiraLocal();
  final CarteiraConfig _config = CarteiraConfig();

  bool _carregando = true;
  String? _erro;
  List<LinhaCarteira> _linhas = [];
  double _variacaoPct = CarteiraConfig.variacaoPadraoPct;

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
      _variacaoPct = await _config.obterVariacaoMonitoramentoPct();
      final posicoes = await _carteira.listar();
      if (posicoes.isEmpty) {
        setState(() {
          _linhas = [];
          _carregando = false;
        });
        return;
      }

      final linhas = <LinhaCarteira>[];
      for (final pos in posicoes) {
        try {
          final cotacao = await _api.obterCotacao(pos.simbolo, tipo: pos.tipo);
          double dividendos = 0;
          var proxData = '';
          double? proxValorCota;
          double? proxTotal;

          if (pos.tipo != TipoAtivo.indices) {
            try {
              final detalhes = await _api.obterDetalhes(
                pos.simbolo,
                tipo: pos.tipo,
              );
              dividendos = DividendosCarteiraHelper.calcularRecebidos(
                pagamentos: detalhes.pagamentosDividendos,
                dataCompraTexto: pos.dataCompra,
                quantidade: pos.quantidade,
              );
              final prox = DividendosCarteiraHelper.estimarProximo(
                pagamentos: detalhes.pagamentosDividendos,
                quantidade: pos.quantidade,
              );
              proxData = prox.data;
              proxValorCota = prox.valorPorCota;
              proxTotal = prox.valorPrevistoTotal;
            } catch (_) {
              // Mantém cotação mesmo sem detalhes/dividendos.
            }
          }

          linhas.add(LinhaCarteira(
            posicao: pos,
            precoAtual: cotacao.preco,
            moeda: cotacao.moeda,
            nomeAtivo: cotacao.nome,
            dividendosRecebidos: dividendos,
            proximoDividendoData: proxData,
            proximoDividendoValorPorCota: proxValorCota,
            proximoDividendoPrevisto: proxTotal,
          ));
        } catch (_) {
          linhas.add(LinhaCarteira(posicao: pos));
        }
      }

      if (!mounted) return;
      setState(() {
        _linhas = linhas;
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

  Future<void> _abrirFormulario({
    PosicaoCarteira? posicao,
    String? preencherSimbolo,
    TipoAtivo? preencherTipo,
  }) async {
    final salvou = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => CarteiraFormTela(
          posicao: posicao,
          preencherSimbolo: preencherSimbolo,
          preencherTipo: preencherTipo,
        ),
      ),
    );
    if (salvou == true) await _carregar();
  }

  Future<void> _configurarVariacao() async {
    final ctrl = TextEditingController(
      text: _variacaoPct.toStringAsFixed(0),
    );

    final novo = await showDialog<double>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Variação do monitoramento'),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(
            labelText: 'Percentual (%)',
            helperText: 'Limites: preço de compra ± este valor',
            border: OutlineInputBorder(),
          ),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          FilledButton(
            onPressed: () {
              final valor = double.tryParse(ctrl.text.replaceAll(',', '.'));
              if (valor == null || valor < 1 || valor > 50) {
                ScaffoldMessenger.of(ctx).showSnackBar(
                  const SnackBar(content: Text('Informe um valor entre 1 e 50.')),
                );
                return;
              }
              Navigator.pop(ctx, valor);
            },
            child: const Text('Salvar'),
          ),
        ],
      ),
    );

    if (novo != null) {
      await _config.salvarVariacaoMonitoramentoPct(novo);
      await _carteira.resincronizarMonitoramentoTodas();
      await _carregar();
    }
  }

  Future<void> _registrarVenda(PosicaoCarteira pos) async {
    final ctrl = TextEditingController();
    final confirmou = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Vender ${pos.simbolo}'),
        content: TextField(
          controller: ctrl,
          decoration: InputDecoration(
            labelText: 'Quantidade a vender (máx. ${pos.quantidade})',
            border: const OutlineInputBorder(),
          ),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Confirmar venda'),
          ),
        ],
      ),
    );

    if (confirmou != true) return;

    try {
      final qtd = double.parse(ctrl.text.trim().replaceAll(',', '.'));
      await _carteira.registrarVenda(id: pos.id, quantidadeVendida: qtd);
      await _carregar();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  Future<void> _excluir(PosicaoCarteira pos) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Excluir posição'),
        content: Text('Remover ${pos.simbolo} da carteira e do monitoramento?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Excluir'),
          ),
        ],
      ),
    );
    if (ok == true) {
      await _carteira.remover(pos.id);
      await _carregar();
    }
  }

  void _abrirGrafico(LinhaCarteira linha) {
    if (linha.precoAtual == null) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => GraficoTela(
          simbolo: linha.posicao.simbolo,
          codigo: linha.posicao.simbolo,
          tipo: linha.tipo,
        ),
      ),
    );
  }

  Widget _resumoGeral() {
    var investido = 0.0;
    var atual = 0.0;
    var dividendos = 0.0;
    var temAtual = false;

    for (final linha in _linhas) {
      investido += linha.posicao.valorInvestido;
      dividendos += linha.dividendosRecebidos;
      if (linha.valorAtual != null) {
        atual += linha.valorAtual!;
        temAtual = true;
      }
    }

    final resultado = temAtual ? atual - investido : null;
    final moeda = _linhas.isNotEmpty ? _linhas.first.moeda : 'BRL';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text('Resumo da carteira', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
                IconButton(
                  tooltip: 'Variação do monitoramento ($_variacaoPct%)',
                  onPressed: _configurarVariacao,
                  icon: const Icon(Icons.tune),
                ),
              ],
            ),
            const SizedBox(height: 8),
            _linhaResumo('Investido', formatarMoeda(investido, moeda)),
            if (temAtual) _linhaResumo('Valor atual', formatarMoeda(atual, moeda)),
            if (resultado != null)
              _linhaResumo(
                'Resultado',
                formatarMoeda(resultado, moeda),
                cor: resultado >= 0 ? CoresApp.sucesso : CoresApp.erro,
              ),
            _linhaResumo('Dividendos recebidos', formatarMoeda(dividendos, moeda)),
            const SizedBox(height: 4),
            Text(
              'Monitoramento: ±${_variacaoPct.toStringAsFixed(0)}% sobre o preço médio de compra',
              style: const TextStyle(fontSize: 12, color: CoresApp.textoSecundario),
            ),
            const SizedBox(height: 4),
            const Text(
              'O mesmo ativo pode ter várias compras (datas e preços diferentes).',
              style: TextStyle(fontSize: 12, color: CoresApp.textoSecundario),
            ),
          ],
        ),
      ),
    );
  }

  Widget _linhaResumo(String rotulo, String valor, {Color? cor}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(rotulo, style: const TextStyle(color: CoresApp.textoSecundario)),
          Text(valor, style: TextStyle(fontWeight: FontWeight.w600, color: cor)),
        ],
      ),
    );
  }

  Widget _cardPosicao(LinhaCarteira linha) {
    final pos = linha.posicao;
    final resultado = linha.resultadoReais;
    final pct = linha.resultadoPercentual;

    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          InkWell(
            onTap: () => _abrirGrafico(linha),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              pos.simbolo,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            if (linha.nomeAtivo.isNotEmpty)
                              Text(
                                linha.nomeAtivo,
                                style: const TextStyle(
                                  color: CoresApp.textoSecundario,
                                  fontSize: 12,
                                ),
                              ),
                            Text(
                              '${pos.tipo.rotulo} · Compra ${pos.dataCompra}',
                              style: const TextStyle(
                                color: CoresApp.textoSecundario,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        tooltip: 'Excluir posição',
                        onPressed: () => _excluir(pos),
                        icon: const Icon(Icons.delete_outline),
                      ),
                    ],
                  ),
                  const Divider(height: 20),
                  _detalhe('Quantidade', pos.quantidade.toString()),
                  _detalhe('Preço compra', formatarMoeda(pos.precoCompra, linha.moeda)),
                  _detalhe('Investido', formatarMoeda(pos.valorInvestido, linha.moeda)),
                  if (linha.precoAtual != null)
                    _detalhe('Preço atual', formatarMoeda(linha.precoAtual!, linha.moeda)),
                  if (linha.valorAtual != null)
                    _detalhe('Valor atual', formatarMoeda(linha.valorAtual!, linha.moeda)),
                  if (resultado != null && pct != null)
                    _detalhe(
                      'Valorização',
                      '${formatarMoeda(resultado, linha.moeda)} (${formatarVariacao(pct)})',
                      cor: resultado >= 0 ? CoresApp.sucesso : CoresApp.erro,
                    ),
                  _detalhe(
                    'Dividendos recebidos',
                    formatarMoeda(linha.dividendosRecebidos, linha.moeda),
                  ),
                  if (linha.proximoDividendoData.isNotEmpty) ...[
                    _detalhe(
                      'Próximo dividendo (est.)',
                      linha.proximoDividendoData,
                    ),
                    if (linha.proximoDividendoPrevisto != null)
                      _detalhe(
                        'Valor previsto',
                        formatarMoeda(linha.proximoDividendoPrevisto!, linha.moeda),
                      ),
                  ],
                ],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
            child: Wrap(
              spacing: 4,
              runSpacing: 4,
              children: [
                TextButton.icon(
                  onPressed: () => _abrirFormulario(
                    preencherSimbolo: pos.simbolo,
                    preencherTipo: pos.tipo,
                  ),
                  icon: const Icon(Icons.add_shopping_cart, size: 18),
                  label: const Text('Nova compra'),
                ),
                TextButton.icon(
                  onPressed: () => _abrirFormulario(posicao: pos),
                  icon: const Icon(Icons.edit_outlined, size: 18),
                  label: const Text('Editar'),
                ),
                TextButton.icon(
                  onPressed: () => _registrarVenda(pos),
                  icon: const Icon(Icons.sell_outlined, size: 18),
                  label: const Text('Vender'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _detalhe(String rotulo, String valor, {Color? cor}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 150,
            child: Text(rotulo, style: const TextStyle(color: CoresApp.textoSecundario, fontSize: 13)),
          ),
          Expanded(
            child: Text(
              valor,
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: cor),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_carregando) {
      return const EstadoCarregando(mensagem: 'Carregando carteira...');
    }
    if (_erro != null) {
      return EstadoErro(mensagem: _erro!, aoTentarNovamente: _carregar);
    }

    return Stack(
      children: [
        RefreshIndicator(
          onRefresh: _carregar,
          child: _linhas.isEmpty
              ? ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  children: const [
                    SizedBox(height: 120),
                    Center(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Text(
                          'Nenhuma posição na carteira.\nToque em + para registrar uma compra.',
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ),
                  ],
                )
              : ListView.builder(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(12, 12, 12, 80),
                  itemCount: _linhas.length + 1,
                  itemBuilder: (context, indice) {
                    if (indice == 0) return _resumoGeral();
                    return Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: _cardPosicao(_linhas[indice - 1]),
                    );
                  },
                ),
        ),
        Positioned(
          right: 16,
          bottom: 16,
          child: FloatingActionButton.extended(
            onPressed: () => _abrirFormulario(),
            icon: const Icon(Icons.add),
            label: const Text('Compra'),
          ),
        ),
      ],
    );
  }
}
