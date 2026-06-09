import 'tipo_ativo.dart';

/// Posição de um ativo na carteira do usuário.
class PosicaoCarteira {
  PosicaoCarteira({
    required this.id,
    required this.tipo,
    required this.simbolo,
    required this.quantidade,
    required this.precoCompra,
    required this.dataCompra,
  });

  final String id;
  final TipoAtivo tipo;
  final String simbolo;
  final double quantidade;
  final double precoCompra;
  final String dataCompra;

  double get valorInvestido => quantidade * precoCompra;

  Map<String, dynamic> paraJson() => {
        'id': id,
        'tipo': tipo.chave,
        'simbolo': simbolo,
        'quantidade': quantidade,
        'precoCompra': precoCompra,
        'dataCompra': dataCompra,
      };

  factory PosicaoCarteira.fromJson(Map<String, dynamic> json) {
    return PosicaoCarteira(
      id: json['id'] as String? ?? '',
      tipo: TipoAtivo.fromChave(json['tipo'] as String? ?? 'acoes'),
      simbolo: (json['simbolo'] as String? ?? '').toUpperCase(),
      quantidade: (json['quantidade'] as num?)?.toDouble() ?? 0,
      precoCompra: (json['precoCompra'] as num?)?.toDouble() ?? 0,
      dataCompra: json['dataCompra'] as String? ?? '',
    );
  }

  PosicaoCarteira copiarCom({
    String? id,
    TipoAtivo? tipo,
    String? simbolo,
    double? quantidade,
    double? precoCompra,
    String? dataCompra,
  }) {
    return PosicaoCarteira(
      id: id ?? this.id,
      tipo: tipo ?? this.tipo,
      simbolo: simbolo ?? this.simbolo,
      quantidade: quantidade ?? this.quantidade,
      precoCompra: precoCompra ?? this.precoCompra,
      dataCompra: dataCompra ?? this.dataCompra,
    );
  }
}
