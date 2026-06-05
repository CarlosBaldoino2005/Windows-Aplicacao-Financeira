class ResultadoBusca {
  ResultadoBusca({
    required this.simbolo,
    required this.codigo,
    required this.nome,
    required this.bolsa,
  });

  final String simbolo;
  final String codigo;
  final String nome;
  final String bolsa;

  factory ResultadoBusca.fromJson(Map<String, dynamic> json) {
    return ResultadoBusca(
      simbolo: json['simbolo'] as String? ?? '',
      codigo: json['codigo'] as String? ?? '',
      nome: json['nome'] as String? ?? '',
      bolsa: json['bolsa'] as String? ?? '',
    );
  }
}
