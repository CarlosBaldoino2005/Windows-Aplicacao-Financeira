class PontoHistorico {
  PontoHistorico({
    required this.dataIso,
    required this.data,
    required this.precoFechamento,
    this.precoAbertura,
    this.volume,
  });

  final String dataIso;
  final String data;
  final double precoFechamento;
  final double? precoAbertura;
  final int? volume;

  factory PontoHistorico.fromJson(Map<String, dynamic> json) {
    return PontoHistorico(
      dataIso: json['dataIso'] as String? ?? '',
      data: json['data'] as String? ?? '',
      precoFechamento: (json['precoFechamento'] as num?)?.toDouble() ?? 0,
      precoAbertura: (json['precoAbertura'] as num?)?.toDouble(),
      volume: json['volume'] as int?,
    );
  }
}

class SerieHistorica {
  SerieHistorica({
    required this.simbolo,
    required this.periodo,
    required this.pontos,
    this.aviso = '',
  });

  final String simbolo;
  final String periodo;
  final List<PontoHistorico> pontos;
  final String aviso;

  factory SerieHistorica.fromJson(Map<String, dynamic> json) {
    final lista = json['pontos'] as List<dynamic>? ?? [];
    return SerieHistorica(
      simbolo: json['simbolo'] as String? ?? '',
      periodo: json['periodo'] as String? ?? '',
      aviso: json['aviso'] as String? ?? '',
      pontos: lista.map((p) => PontoHistorico.fromJson(p as Map<String, dynamic>)).toList(),
    );
  }
}
