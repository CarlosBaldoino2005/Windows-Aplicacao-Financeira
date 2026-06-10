import 'package:flutter/material.dart';

import '../modelos/posicao_carteira.dart';
import '../modelos/resultado_busca.dart';
import '../modelos/tipo_ativo.dart';
import '../servicos/api_cliente.dart';
import '../servicos/carteira_local.dart';
import '../tema/cores.dart';
import '../util/validadores_carteira.dart';
import '../widgets/seletor_tipo_ativo.dart';

/// Formulário para cadastrar ou editar posição na carteira.
class CarteiraFormTela extends StatefulWidget {
  const CarteiraFormTela({super.key, this.posicao});

  final PosicaoCarteira? posicao;

  @override
  State<CarteiraFormTela> createState() => _CarteiraFormTelaState();
}

class _CarteiraFormTelaState extends State<CarteiraFormTela> {
  final _formKey = GlobalKey<FormState>();
  final _carteira = CarteiraLocal();
  final _api = ApiCliente();

  late TipoAtivo _tipo;
  final _buscaCtrl = TextEditingController();
  final _quantidadeCtrl = TextEditingController();
  final _precoCtrl = TextEditingController();
  final _dataCtrl = TextEditingController();

  String? _simboloSelecionado;
  String? _codigoSelecionado;
  bool _salvando = false;
  bool _buscando = false;
  String? _erroBusca;
  List<ResultadoBusca> _resultados = [];

  bool get _editando => widget.posicao != null;

  String get _dicaBusca {
    return switch (_tipo) {
      TipoAtivo.cripto => 'BTC, ETH, SOL...',
      TipoAtivo.fiis => 'HGLG11, KNCR11...',
      TipoAtivo.indices => 'IBOV, IFIX...',
      TipoAtivo.acoes => 'PETR4, Vale, AAPL...',
    };
  }

  @override
  void initState() {
    super.initState();
    final pos = widget.posicao;
    _tipo = pos?.tipo ?? TipoAtivo.acoes;
    if (pos != null) {
      _simboloSelecionado = pos.simbolo;
      _codigoSelecionado = ValidadoresCarteira.codigoExibicao(pos.simbolo);
      _quantidadeCtrl.text = pos.quantidade.toString();
      _precoCtrl.text = pos.precoCompra.toStringAsFixed(2).replaceAll('.', ',');
      _dataCtrl.text = pos.dataCompra;
    } else {
      _dataCtrl.text = ValidadoresCarteira.dataHoje();
    }
  }

  @override
  void dispose() {
    _buscaCtrl.dispose();
    _quantidadeCtrl.dispose();
    _precoCtrl.dispose();
    _dataCtrl.dispose();
    super.dispose();
  }

  void _mudarTipo(TipoAtivo novo) {
    setState(() {
      _tipo = novo;
      _simboloSelecionado = null;
      _codigoSelecionado = null;
      _resultados = [];
      _erroBusca = null;
      _buscaCtrl.clear();
    });
  }

  void _limparSelecao() {
    setState(() {
      _simboloSelecionado = null;
      _codigoSelecionado = null;
    });
  }

  Future<void> _pesquisar() async {
    if (_tipo == TipoAtivo.indices) {
      setState(() {
        _erroBusca = 'Para índices, digite o código (ex.: ^BVSP) ou busque na aba Painel.';
        _resultados = [];
      });
      return;
    }

    final termo = _buscaCtrl.text.trim();
    if (termo.length < 2) {
      setState(() {
        _erroBusca = 'Digite ao menos 2 caracteres.';
        _resultados = [];
      });
      return;
    }

    setState(() {
      _buscando = true;
      _erroBusca = null;
    });

    try {
      final lista = await _api.buscar(termo, tipo: _tipo);
      if (!mounted) return;
      setState(() {
        _resultados = lista;
        _buscando = false;
        if (lista.length == 1) {
          _aplicarSelecao(lista.first);
        }
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _erroBusca = e.toString().replaceFirst('Exception: ', '');
        _resultados = [];
        _buscando = false;
      });
    }
  }

  void _aplicarSelecao(ResultadoBusca item) {
    _simboloSelecionado = item.simbolo;
    _codigoSelecionado = item.codigo.isNotEmpty
        ? item.codigo
        : ValidadoresCarteira.codigoExibicao(item.simbolo);
  }

  void _selecionarResultado(ResultadoBusca item) {
    setState(() => _aplicarSelecao(item));
  }

  Future<void> _escolherDataCompra() async {
    final hoje = DateTime.now();
    final inicial = ValidadoresCarteira.parseData(_dataCtrl.text) ?? hoje;
    final escolhida = await showDatePicker(
      context: context,
      initialDate: inicial.isAfter(hoje) ? hoje : inicial,
      firstDate: DateTime(1900),
      lastDate: hoje,
      helpText: 'Data da compra',
      cancelText: 'Cancelar',
      confirmText: 'OK',
    );
    if (escolhida != null && mounted) {
      setState(() {
        _dataCtrl.text = ValidadoresCarteira.formatarData(escolhida);
      });
    }
  }

  String? _resolverSimbolo() {
    if (_simboloSelecionado != null && _simboloSelecionado!.isNotEmpty) {
      return _simboloSelecionado;
    }
    final digitado = _buscaCtrl.text.trim();
    if (digitado.isEmpty) return null;
    return ValidadoresCarteira.normalizarSimbolo(digitado, _tipo);
  }

  Future<void> _salvar() async {
    if (!_formKey.currentState!.validate()) return;

    final simbolo = _resolverSimbolo();
    if (simbolo == null || simbolo.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecione um ativo na busca ou digite o código.')),
      );
      return;
    }

    setState(() => _salvando = true);
    try {
      final quantidade = ValidadoresCarteira.parseQuantidade(_quantidadeCtrl.text)!;
      final preco = ValidadoresCarteira.parsePreco(_precoCtrl.text)!;
      final data = _dataCtrl.text.trim();

      if (widget.posicao == null) {
        await _carteira.adicionar(
          tipo: _tipo,
          simbolo: simbolo,
          quantidade: quantidade,
          precoCompra: preco,
          dataCompra: data,
        );
      } else {
        await _carteira.atualizar(
          widget.posicao!.copiarCom(
            tipo: _tipo,
            simbolo: simbolo,
            quantidade: quantidade,
            precoCompra: preco,
            dataCompra: data,
          ),
        );
      }

      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) setState(() => _salvando = false);
    }
  }

  Widget _montarBuscaAtivo() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Buscar ativo',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _buscaCtrl,
                decoration: InputDecoration(
                  labelText: 'Código ou nome',
                  hintText: _dicaBusca,
                  border: const OutlineInputBorder(),
                  isDense: true,
                ),
                textCapitalization: TextCapitalization.characters,
                textInputAction: TextInputAction.search,
                onFieldSubmitted: (_) => _pesquisar(),
              ),
            ),
            const SizedBox(width: 8),
            FilledButton(
              onPressed: _buscando ? null : _pesquisar,
              child: _buscando
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Buscar'),
            ),
          ],
        ),
        if (_erroBusca != null) ...[
          const SizedBox(height: 8),
          Text(_erroBusca!, style: const TextStyle(color: CoresApp.erro)),
        ],
        if (_resultados.isNotEmpty) ...[
          const SizedBox(height: 8),
          const Text('Resultados', style: TextStyle(fontSize: 12)),
          const SizedBox(height: 4),
          ..._resultados.take(8).map((item) {
            final codigo = item.codigo.isNotEmpty
                ? item.codigo
                : ValidadoresCarteira.codigoExibicao(item.simbolo);
            final selecionado = _simboloSelecionado == item.simbolo;
            return Card(
              margin: const EdgeInsets.only(bottom: 4),
              color: selecionado
                  ? Theme.of(context).colorScheme.primaryContainer
                  : null,
              child: ListTile(
                dense: true,
                title: Text(
                  codigo,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                subtitle: Text(item.nome, maxLines: 1, overflow: TextOverflow.ellipsis),
                onTap: () => _selecionarResultado(item),
              ),
            );
          }),
        ],
        const SizedBox(height: 8),
        if (_codigoSelecionado != null)
          Row(
            children: [
              Expanded(
                child: Text(
                  'Selecionado: $_codigoSelecionado',
                  style: const TextStyle(
                    color: CoresApp.sucesso,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              TextButton(
                onPressed: _limparSelecao,
                child: const Text('Limpar'),
              ),
            ],
          )
        else
          const Text(
            'Nenhum ativo selecionado. Busque acima ou digite o código e salve.',
            style: TextStyle(fontSize: 12, color: CoresApp.textoSecundario),
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_editando ? 'Editar posição' : 'Nova compra'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            SeletorTipoAtivo(
              tipoSelecionado: _tipo,
              aoMudar: _editando ? (_) {} : _mudarTipo,
            ),
            const SizedBox(height: 16),
            if (_editando)
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Ativo'),
                subtitle: Text(
                  _codigoSelecionado ?? '',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              )
            else
              _montarBuscaAtivo(),
            const SizedBox(height: 12),
            TextFormField(
              controller: _quantidadeCtrl,
              decoration: const InputDecoration(
                labelText: 'Quantidade',
                border: OutlineInputBorder(),
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              validator: (v) => ValidadoresCarteira.validarQuantidade(v ?? ''),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _precoCtrl,
              decoration: const InputDecoration(
                labelText: 'Preço pago (por cota/unidade)',
                hintText: 'Ex.: 32,45',
                border: OutlineInputBorder(),
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              validator: (v) => ValidadoresCarteira.validarPreco(v ?? ''),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _dataCtrl,
              readOnly: true,
              onTap: _escolherDataCompra,
              decoration: const InputDecoration(
                labelText: 'Data da compra',
                hintText: 'dd/mm/aaaa',
                border: OutlineInputBorder(),
                suffixIcon: Icon(Icons.calendar_today),
              ),
              validator: (v) => ValidadoresCarteira.validarDataCompra(v ?? ''),
            ),
            const SizedBox(height: 8),
            const Text(
              'Ao salvar, o ativo entra no monitoramento com limites de ±10% sobre o preço de compra (ajustável na carteira).',
              style: TextStyle(fontSize: 12),
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: _salvando ? null : _salvar,
              icon: _salvando
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.save),
              label: Text(_editando ? 'Salvar alterações' : 'Adicionar à carteira'),
            ),
          ],
        ),
      ),
    );
  }
}
