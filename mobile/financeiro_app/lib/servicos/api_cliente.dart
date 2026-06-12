import '../modelos/cotacao_resumo.dart';
import '../modelos/detalhes_ativo.dart';
import '../modelos/resultado_busca.dart';
import '../modelos/serie_historica.dart';
import '../modelos/tipo_ativo.dart';
import 'busca_mercado_servico.dart';
import 'detalhes_mercado_servico.dart';
import 'mercado_servico.dart';
import 'provedores/yahoo_chart_provedor.dart';

/// Cliente de mercado: consulta Yahoo/Brapi direto (como o desktop), sem API local.
class ApiCliente {
  ApiCliente({
    MercadoServico? mercado,
    BuscaMercadoServico? busca,
    DetalhesMercadoServico? detalhes,
    YahooChartProvedor? yahooChart,
  })  : _mercado = mercado ?? MercadoServico(),
        _busca = busca ?? BuscaMercadoServico(),
        _detalhes = detalhes ?? DetalhesMercadoServico(),
        _yahooChart = yahooChart ?? YahooChartProvedor();

  final MercadoServico _mercado;
  final BuscaMercadoServico _busca;
  final DetalhesMercadoServico _detalhes;
  final YahooChartProvedor _yahooChart;

  /// Versao logica do app mobile (nao depende mais da API FastAPI).
  static const String versaoApi = '1.1.0';

  static const List<String> recursosApi = [
    'painel-acoes',
    'painel-cripto',
    'painel-fiis',
    'painel-indices',
    'detalhes',
    'historico',
    'busca-cripto',
    'busca-fiis',
  ];

  static bool get suportaPainelCompleto => true;

  /// Verifica se os provedores de mercado respondem (internet + Yahoo).
  Future<void> verificarSaude() async {
    final resumo = await _yahooChart.buscarResumos(['SPY']);
    if (resumo.isEmpty) {
      throw Exception('Provedores de mercado indisponiveis.');
    }
  }

  static String mensagemApiDesatualizada(TipoAtivo tipo) {
    return 'Recurso ${tipo.rotulo} indisponivel nesta versao do app.';
  }

  static bool tipoExigeApiRecente(TipoAtivo tipo) => false;

  Future<Map<String, List<CotacaoResumo>>> obterPainel({
    TipoAtivo tipo = TipoAtivo.acoes,
    int quantidade = 10,
  }) {
    return _mercado.obterPainel(tipo: tipo, quantidade: quantidade);
  }

  Future<CotacaoResumo> obterCotacao(String simbolo, {TipoAtivo tipo = TipoAtivo.acoes}) {
    return _mercado.obterCotacao(simbolo, tipo);
  }

  Future<SerieHistorica> obterHistorico(
    String simbolo, {
    TipoAtivo tipo = TipoAtivo.acoes,
    String periodo = 'mes',
  }) {
    return _mercado.obterHistorico(simbolo, tipo, periodo: periodo);
  }

  Future<DetalhesAtivo> obterDetalhes(String simbolo, {TipoAtivo tipo = TipoAtivo.acoes}) {
    return _detalhes.obterDetalhes(simbolo, tipo);
  }

  Future<List<ResultadoBusca>> buscar(String termo, {TipoAtivo tipo = TipoAtivo.acoes}) {
    return _busca.buscar(termo, tipo);
  }
}
