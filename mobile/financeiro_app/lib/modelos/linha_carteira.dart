import 'posicao_carteira.dart';
import 'tipo_ativo.dart';

/// Posição da carteira enriquecida com cotação e dividendos.
class LinhaCarteira {
  LinhaCarteira({
    required this.posicao,
    this.precoAtual,
    this.moeda = 'BRL',
    this.nomeAtivo = '',
    this.dividendosRecebidos = 0,
    this.proximoDividendoData = '',
    this.proximoDividendoValorPorCota,
    this.proximoDividendoPrevisto,
  });

  final PosicaoCarteira posicao;
  final double? precoAtual;
  final String moeda;
  final String nomeAtivo;
  final double dividendosRecebidos;
  final String proximoDividendoData;
  final double? proximoDividendoValorPorCota;
  final double? proximoDividendoPrevisto;

  TipoAtivo get tipo => posicao.tipo;

  double? get valorAtual =>
      precoAtual != null ? posicao.quantidade * precoAtual! : null;

  double? get resultadoReais =>
      valorAtual != null ? valorAtual! - posicao.valorInvestido : null;

  double? get resultadoPercentual {
    if (posicao.valorInvestido <= 0 || resultadoReais == null) return null;
    return (resultadoReais! / posicao.valorInvestido) * 100;
  }
}
