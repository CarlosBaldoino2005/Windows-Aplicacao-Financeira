import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../modelos/posicao_carteira.dart';
import '../modelos/tipo_ativo.dart';
import '../servicos/carteira_local.dart';
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

  late TipoAtivo _tipo;
  final _simboloCtrl = TextEditingController();
  final _quantidadeCtrl = TextEditingController();
  final _precoCtrl = TextEditingController();
  final _dataCtrl = TextEditingController();

  bool _salvando = false;

  @override
  void initState() {
    super.initState();
    final pos = widget.posicao;
    _tipo = pos?.tipo ?? TipoAtivo.acoes;
    if (pos != null) {
      _simboloCtrl.text = pos.simbolo;
      _quantidadeCtrl.text = pos.quantidade.toString();
      _precoCtrl.text = pos.precoCompra.toStringAsFixed(2).replaceAll('.', ',');
      _dataCtrl.text = pos.dataCompra;
    }
  }

  @override
  void dispose() {
    _simboloCtrl.dispose();
    _quantidadeCtrl.dispose();
    _precoCtrl.dispose();
    _dataCtrl.dispose();
    super.dispose();
  }

  Future<void> _salvar() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _salvando = true);
    try {
      final quantidade = ValidadoresCarteira.parseQuantidade(_quantidadeCtrl.text)!;
      final preco = ValidadoresCarteira.parsePreco(_precoCtrl.text)!;
      final data = _dataCtrl.text.trim();
      final simbolo = _simboloCtrl.text.trim().toUpperCase();

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

  @override
  Widget build(BuildContext context) {
    final editando = widget.posicao != null;

    return Scaffold(
      appBar: AppBar(
        title: Text(editando ? 'Editar posição' : 'Nova compra'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            SeletorTipoAtivo(
              tipoSelecionado: _tipo,
              aoMudar: (tipo) => setState(() => _tipo = tipo),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _simboloCtrl,
              decoration: const InputDecoration(
                labelText: 'Código do ativo',
                hintText: 'Ex.: PETR4.SA, BTC-USD, HGLG11.SA',
                border: OutlineInputBorder(),
              ),
              textCapitalization: TextCapitalization.characters,
              validator: (v) => ValidadoresCarteira.validarSimbolo(v ?? ''),
            ),
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
              decoration: const InputDecoration(
                labelText: 'Data da compra',
                hintText: 'dd/mm/aaaa',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.datetime,
              inputFormatters: [
                FilteringTextInputFormatter.allow(RegExp(r'[0-9/]')),
              ],
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
              label: Text(editando ? 'Salvar alterações' : 'Adicionar à carteira'),
            ),
          ],
        ),
      ),
    );
  }
}
