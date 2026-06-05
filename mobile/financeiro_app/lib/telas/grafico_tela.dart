import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../modelos/cotacao_resumo.dart';
import '../modelos/serie_historica.dart';
import '../modelos/tipo_ativo.dart';
import '../servicos/api_cliente.dart';
import '../tema/cores.dart';
import '../util/formatadores.dart';
import '../widgets/estado_carregando.dart';
import '../widgets/estado_erro.dart';
import 'detalhes_tela.dart';

/// Grafico de historico de preco com seletor de periodo.
class GraficoTela extends StatefulWidget {
  const GraficoTela({
    super.key,
    required this.simbolo,
    required this.codigo,
    required this.tipo,
    this.cotacao,
  });

  final String simbolo;
  final String codigo;
  final TipoAtivo tipo;
  final CotacaoResumo? cotacao;

  @override
  State<GraficoTela> createState() => _GraficoTelaState();
}

class _GraficoTelaState extends State<GraficoTela> {
  final ApiCliente _api = ApiCliente();

  static const _periodos = [
    ('dia', 'Dia'),
    ('semana', 'Semana'),
    ('mes', 'Mês'),
    ('trimestre', 'Trimestre'),
    ('semestre', 'Semestre'),
    ('ano', 'Ano'),
  ];

  String _periodo = 'mes';
  bool _carregando = true;
  String? _erro;
  SerieHistorica? _serie;

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
      final serie = await _api.obterHistorico(
        widget.simbolo,
        tipo: widget.tipo,
        periodo: _periodo,
      );
      if (!mounted) return;
      setState(() {
        _serie = serie;
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

  void _abrirDetalhes() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => DetalhesTela(
          simbolo: widget.simbolo,
          codigo: widget.codigo,
          tipo: widget.tipo,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cotacao = widget.cotacao;
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.codigo),
        actions: [
          if (widget.tipo != TipoAtivo.indices)
            IconButton(
              tooltip: 'Mais detalhes',
              onPressed: _abrirDetalhes,
              icon: const Icon(Icons.info_outline),
            ),
        ],
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (cotacao != null)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          formatarMoeda(cotacao.preco, cotacao.moeda),
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          formatarVariacao(cotacao.variacaoPercentual),
                          style: TextStyle(
                            color: cotacao.variacaoPercentual >= 0
                                ? CoresApp.sucesso
                                : CoresApp.erro,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: _periodos.map((item) {
                final selecionado = item.$1 == _periodo;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(item.$2),
                    selected: selecionado,
                    onSelected: (_) {
                      setState(() => _periodo = item.$1);
                      _carregar();
                    },
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: _carregando
                ? const EstadoCarregando(mensagem: 'Carregando gráfico...')
                : _erro != null
                    ? EstadoErro(mensagem: _erro!, aoTentarNovamente: _carregar)
                    : _montarGrafico(),
          ),
        ],
      ),
    );
  }

  Widget _montarGrafico() {
    final pontos = _serie?.pontos ?? [];
    if (pontos.isEmpty) {
      return const Center(child: Text('Sem dados para este periodo.'));
    }

    final spots = <FlSpot>[];
    for (var i = 0; i < pontos.length; i++) {
      spots.add(FlSpot(i.toDouble(), pontos[i].precoFechamento));
    }

    final minY = spots.map((s) => s.y).reduce((a, b) => a < b ? a : b);
    final maxY = spots.map((s) => s.y).reduce((a, b) => a > b ? a : b);
    final subiu = pontos.last.precoFechamento >= pontos.first.precoFechamento;
    final corLinha = subiu ? CoresApp.sucesso : CoresApp.erro;

    return Padding(
      padding: const EdgeInsets.all(16),
      child: LineChart(
        LineChartData(
          minY: minY * 0.98,
          maxY: maxY * 1.02,
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: (maxY - minY) / 4,
          ),
          titlesData: FlTitlesData(
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 56,
                getTitlesWidget: (valor, _) => Text(
                  valor.toStringAsFixed(0),
                  style: const TextStyle(fontSize: 10, color: CoresApp.textoSecundario),
                ),
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 28,
                interval: (pontos.length / 4).clamp(1, pontos.length).toDouble(),
                getTitlesWidget: (valor, _) {
                  final indice = valor.toInt();
                  if (indice < 0 || indice >= pontos.length) return const SizedBox.shrink();
                  return Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Text(
                      pontos[indice].data,
                      style: const TextStyle(fontSize: 10, color: CoresApp.textoSecundario),
                    ),
                  );
                },
              ),
            ),
          ),
          borderData: FlBorderData(show: false),
          lineBarsData: [
            LineChartBarData(
              spots: spots,
              isCurved: true,
              color: corLinha,
              barWidth: 2.5,
              dotData: const FlDotData(show: false),
              belowBarData: BarAreaData(
                show: true,
                color: corLinha.withValues(alpha: 0.12),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
