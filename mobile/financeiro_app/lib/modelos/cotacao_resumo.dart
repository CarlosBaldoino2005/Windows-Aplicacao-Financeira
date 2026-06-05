class CotacaoResumo {
  CotacaoResumo({
    required this.simbolo,
    required this.codigo,
    required this.nome,
    required this.preco,
    required this.variacaoPercentual,
    required this.variacaoValor,
    required this.moeda,
    this.volume,
  });

  final String simbolo;
  final String codigo;
  final String nome;
  final double preco;
  final double variacaoPercentual;
  final double variacaoValor;
  final String moeda;
  final int? volume;

  factory CotacaoResumo.fromJson(Map<String, dynamic> json) {
    return CotacaoResumo(
      simbolo: json['simbolo'] as String? ?? '',
      codigo: json['codigo'] as String? ?? '',
      nome: json['nome'] as String? ?? '',
      preco: (json['preco'] as num?)?.toDouble() ?? 0,
      variacaoPercentual: (json['variacaoPercentual'] as num?)?.toDouble() ?? 0,
      variacaoValor: (json['variacaoValor'] as num?)?.toDouble() ?? 0,
      moeda: json['moeda'] as String? ?? 'BRL',
      volume: json['volume'] as int?,
    );
  }
}
