/// Tipos de ativo suportados no app mobile.
enum TipoAtivo {
  acoes('acoes', 'Ações'),
  cripto('cripto', 'Cripto'),
  fiis('fiis', 'FIIs'),
  indices('indices', 'Índices');

  const TipoAtivo(this.chave, this.rotulo);

  final String chave;
  final String rotulo;

  static TipoAtivo fromChave(String valor) {
    return TipoAtivo.values.firstWhere(
      (item) => item.chave == valor,
      orElse: () => TipoAtivo.acoes,
    );
  }

  /// Valor enviado na API de detalhes.
  String get parametroDetalhes {
    switch (this) {
      case TipoAtivo.cripto:
        return 'cripto';
      case TipoAtivo.fiis:
        return 'fii';
      case TipoAtivo.indices:
        return 'acao';
      case TipoAtivo.acoes:
        return 'auto';
    }
  }
}
