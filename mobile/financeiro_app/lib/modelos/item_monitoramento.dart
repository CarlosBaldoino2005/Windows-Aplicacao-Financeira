import 'tipo_ativo.dart';

/// Limite de preço para monitoramento de um ativo.
class ItemMonitoramento {
  ItemMonitoramento({
    required this.id,
    required this.tipo,
    required this.simbolo,
    this.valorBaixo,
    this.valorAlto,
    this.pausado = false,
  });

  final String id;
  final TipoAtivo tipo;
  final String simbolo;
  final double? valorBaixo;
  final double? valorAlto;
  final bool pausado;

  Map<String, dynamic> paraJson() => {
        'id': id,
        'tipo': tipo.chave,
        'simbolo': simbolo,
        'valorBaixo': valorBaixo,
        'valorAlto': valorAlto,
        'pausado': pausado,
      };

  factory ItemMonitoramento.fromJson(Map<String, dynamic> json) {
    return ItemMonitoramento(
      id: json['id'] as String? ?? '',
      tipo: TipoAtivo.fromChave(json['tipo'] as String? ?? 'acoes'),
      simbolo: (json['simbolo'] as String? ?? '').toUpperCase(),
      valorBaixo: (json['valorBaixo'] as num?)?.toDouble(),
      valorAlto: (json['valorAlto'] as num?)?.toDouble(),
      pausado: json['pausado'] as bool? ?? false,
    );
  }
}
