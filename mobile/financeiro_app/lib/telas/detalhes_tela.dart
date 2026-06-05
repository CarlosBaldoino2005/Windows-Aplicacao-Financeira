import 'package:flutter/material.dart';

import '../modelos/detalhes_ativo.dart';
import '../modelos/tipo_ativo.dart';
import '../servicos/api_cliente.dart';
import '../tema/cores.dart';
import '../util/formatadores.dart';
import '../widgets/estado_carregando.dart';
import '../widgets/estado_erro.dart';

/// Tela de detalhes da empresa, FII ou criptomoeda.
class DetalhesTela extends StatefulWidget {
  const DetalhesTela({
    super.key,
    required this.simbolo,
    required this.codigo,
    required this.tipo,
  });

  final String simbolo;
  final String codigo;
  final TipoAtivo tipo;

  @override
  State<DetalhesTela> createState() => _DetalhesTelaState();
}

class _DetalhesTelaState extends State<DetalhesTela> with SingleTickerProviderStateMixin {
  final ApiCliente _api = ApiCliente();

  TabController? _abas;
  bool _carregando = true;
  String? _erro;
  DetalhesAtivo? _detalhes;

  @override
  void dispose() {
    _abas?.dispose();
    super.dispose();
  }

  void _configurarAbas(DetalhesAtivo detalhes) {
    _abas?.dispose();
    final quantidade = detalhes.ehCripto ? 3 : 4;
    _abas = TabController(length: quantidade, vsync: this);
  }

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
      final detalhes = await _api.obterDetalhes(widget.simbolo, tipo: widget.tipo);
      if (!mounted) return;
      _configurarAbas(detalhes);
      setState(() {
        _detalhes = detalhes;
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.codigo),
        bottom: _carregando || _erro != null || _abas == null
            ? null
            : TabBar(
                controller: _abas,
                isScrollable: true,
                tabs: [
                  Tab(text: _detalhes!.ehCripto ? 'Ativo' : 'Empresa'),
                  const Tab(text: 'Indicadores'),
                  if (!_detalhes!.ehCripto) const Tab(text: 'Dividendos'),
                  const Tab(text: 'Resultados'),
                ],
              ),
      ),
      body: _carregando
          ? const EstadoCarregando(mensagem: 'Carregando detalhes...')
          : _erro != null
              ? EstadoErro(mensagem: _erro!, aoTentarNovamente: _carregar)
              : _montarConteudo(),
    );
  }

  Widget _montarConteudo() {
    final d = _detalhes!;
    final abas = <Widget>[
      _abaEmpresa(d),
      _abaIndicadores(d),
      if (!d.ehCripto) _abaDividendos(d),
      _abaResultados(d),
    ];

    return TabBarView(
      controller: _abas!,
      children: abas,
    );
  }

  Widget _abaEmpresa(DetalhesAtivo d) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          d.nomeEmpresa,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        if (d.precoAtual != null) ...[
          const SizedBox(height: 8),
          Text(
            formatarMoeda(d.precoAtual!, d.moeda),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
          if (d.variacaoDiaPct != null)
            Text(
              formatarVariacao(d.variacaoDiaPct!),
              style: TextStyle(
                color: d.variacaoDiaPct! >= 0 ? CoresApp.sucesso : CoresApp.erro,
              ),
            ),
        ],
        const SizedBox(height: 16),
        if (d.setor.isNotEmpty) _linhaInfo('Setor', d.setor),
        if (d.industria.isNotEmpty) _linhaInfo('Indústria', d.industria),
        if (d.pais.isNotEmpty) _linhaInfo('País', d.pais),
        if (d.bolsa.isNotEmpty) _linhaInfo('Bolsa', d.bolsa),
        if (d.cnpj.isNotEmpty) _linhaInfo('CNPJ', d.cnpj),
        if (d.site.isNotEmpty) _linhaInfo('Site', d.site),
        if (d.siteRi.isNotEmpty) _linhaInfo('Site RI', d.siteRi),
        if (d.telefone.isNotEmpty) _linhaInfo('Telefone', d.telefone),
        if (d.funcionarios != null) _linhaInfo('Funcionários', d.funcionarios.toString()),
        if (d.enderecoLinha1.isNotEmpty || d.cidade.isNotEmpty)
          _linhaInfo(
            'Endereço',
            [d.enderecoLinha1, d.enderecoLinha2, d.cidade, d.estado, d.cep]
                .where((e) => e.isNotEmpty)
                .join(', '),
          ),
        if (d.descricao.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text('Descrição', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          Text(d.descricao, style: const TextStyle(height: 1.4)),
        ],
        if (d.dirigentes.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text('Dirigentes', style: TextStyle(fontWeight: FontWeight.bold)),
          ...d.dirigentes.map(
            (item) => ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              title: Text(item['nome'] ?? ''),
              subtitle: Text(item['cargo'] ?? ''),
            ),
          ),
        ],
        if (d.opinioesAnalistas != null) ...[
          const SizedBox(height: 16),
          const Text('Opiniões de analistas', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          _linhaInfo('Recomendação', d.opinioesAnalistas!['notaMediaTexto']?.toString() ?? '-'),
          _linhaInfo('Analistas', d.opinioesAnalistas!['totalAnalistas']?.toString() ?? '-'),
        ],
        if (d.avisos.isNotEmpty) ...[
          const SizedBox(height: 16),
          ...d.avisos.map(
            (aviso) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text(aviso, style: const TextStyle(fontSize: 12, color: CoresApp.textoSecundario)),
            ),
          ),
        ],
      ],
    );
  }

  Widget _abaIndicadores(DetalhesAtivo d) {
    if (d.indicadores.isEmpty && d.calculosIndicadores.isEmpty) {
      return const Center(child: Text('Indicadores indisponíveis.'));
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        ...d.indicadores.map(
          (item) => _linhaInfo(item['rotulo'] ?? '', item['valor'] ?? '-'),
        ),
        if (d.calculosIndicadores.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text('Cálculos', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ...d.calculosIndicadores.entries.map(
            (e) => _linhaInfo(e.key, e.value),
          ),
        ],
      ],
    );
  }

  Widget _abaDividendos(DetalhesAtivo d) {
    if (d.pagamentosDividendos.isEmpty) {
      return const Center(child: Text('Nenhum dividendo registrado.'));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: d.pagamentosDividendos.length,
      itemBuilder: (context, indice) {
        final item = d.pagamentosDividendos[indice];
        final valor = (item['valorPorCota'] as num?)?.toDouble();
        return ListTile(
          title: Text(item['dataPagamento']?.toString() ?? ''),
          trailing: Text(
            valor != null ? formatarMoeda(valor, d.moeda) : '-',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        );
      },
    );
  }

  Widget _abaResultados(DetalhesAtivo d) {
    final trimestres = d.trimestres;
    final anuais = d.anuais;
    if (trimestres.isEmpty && anuais.isEmpty) {
      return const Center(child: Text('Resultados financeiros indisponíveis.'));
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (trimestres.isNotEmpty) ...[
          const Text('Trimestres', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ...trimestres.map((t) => _cardResultado(t, d.moeda)),
        ],
        if (anuais.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text('Anuais', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ...anuais.map((a) => _cardResultado(a, d.moeda)),
        ],
      ],
    );
  }

  Widget _cardResultado(Map<String, dynamic> item, String moeda) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              item['periodo']?.toString() ?? '',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            if (item['receita'] != null)
              _linhaInfo('Receita', formatarMoeda((item['receita'] as num).toDouble(), moeda)),
            if (item['lucroLiquido'] != null)
              _linhaInfo(
                'Lucro líquido',
                formatarMoeda((item['lucroLiquido'] as num).toDouble(), moeda),
              ),
          ],
        ),
      ),
    );
  }

  Widget _linhaInfo(String rotulo, String valor) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              rotulo,
              style: const TextStyle(color: CoresApp.textoSecundario),
            ),
          ),
          Expanded(child: Text(valor)),
        ],
      ),
    );
  }
}
