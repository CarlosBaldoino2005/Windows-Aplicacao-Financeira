class DetalhesAtivo {
  DetalhesAtivo({
    required this.simbolo,
    required this.codigo,
    required this.moeda,
    required this.nomeEmpresa,
    this.setor = '',
    this.industria = '',
    this.pais = '',
    this.site = '',
    this.siteRi = '',
    this.descricao = '',
    this.cnpj = '',
    this.enderecoLinha1 = '',
    this.enderecoLinha2 = '',
    this.cidade = '',
    this.estado = '',
    this.cep = '',
    this.telefone = '',
    this.bolsa = '',
    this.dirigentes = const [],
    this.filiais = const [],
    this.funcionarios,
    this.precoAtual,
    this.variacaoDiaPct,
    this.indicadores = const [],
    this.calculosIndicadores = const {},
    this.trimestres = const [],
    this.anuais = const [],
    this.pagamentosDividendos = const [],
    this.concorrentes = const [],
    this.avisos = const [],
    this.ehCripto = false,
    this.opinioesAnalistas,
  });

  final String simbolo;
  final String codigo;
  final String moeda;
  final String nomeEmpresa;
  final String setor;
  final String industria;
  final String pais;
  final String site;
  final String siteRi;
  final String descricao;
  final String cnpj;
  final String enderecoLinha1;
  final String enderecoLinha2;
  final String cidade;
  final String estado;
  final String cep;
  final String telefone;
  final String bolsa;
  final List<Map<String, String>> dirigentes;
  final List<String> filiais;
  final int? funcionarios;
  final double? precoAtual;
  final double? variacaoDiaPct;
  final List<Map<String, String>> indicadores;
  final Map<String, String> calculosIndicadores;
  final List<Map<String, dynamic>> trimestres;
  final List<Map<String, dynamic>> anuais;
  final List<Map<String, dynamic>> pagamentosDividendos;
  final List<Map<String, dynamic>> concorrentes;
  final List<String> avisos;
  final bool ehCripto;
  final Map<String, dynamic>? opinioesAnalistas;

  factory DetalhesAtivo.fromJson(Map<String, dynamic> json) {
    return DetalhesAtivo(
      simbolo: json['simbolo'] as String? ?? '',
      codigo: json['codigo'] as String? ?? '',
      moeda: json['moeda'] as String? ?? 'BRL',
      nomeEmpresa: json['nomeEmpresa'] as String? ?? '',
      setor: json['setor'] as String? ?? '',
      industria: json['industria'] as String? ?? '',
      pais: json['pais'] as String? ?? '',
      site: json['site'] as String? ?? '',
      siteRi: json['siteRi'] as String? ?? '',
      descricao: json['descricao'] as String? ?? '',
      cnpj: json['cnpj'] as String? ?? '',
      enderecoLinha1: json['enderecoLinha1'] as String? ?? '',
      enderecoLinha2: json['enderecoLinha2'] as String? ?? '',
      cidade: json['cidade'] as String? ?? '',
      estado: json['estado'] as String? ?? '',
      cep: json['cep'] as String? ?? '',
      telefone: json['telefone'] as String? ?? '',
      bolsa: json['bolsa'] as String? ?? '',
      dirigentes: _listaMapasString(json['dirigentes']),
      filiais: (json['filiais'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
      funcionarios: json['funcionarios'] as int?,
      precoAtual: (json['precoAtual'] as num?)?.toDouble(),
      variacaoDiaPct: (json['variacaoDiaPct'] as num?)?.toDouble(),
      indicadores: _listaMapasString(json['indicadores']),
      calculosIndicadores: Map<String, String>.from(
        (json['calculosIndicadores'] as Map<String, dynamic>? ?? {}).map(
          (k, v) => MapEntry(k, v?.toString() ?? ''),
        ),
      ),
      trimestres: _listaMapasDinamicos(json['trimestres']),
      anuais: _listaMapasDinamicos(json['anuais']),
      pagamentosDividendos: _listaMapasDinamicos(json['pagamentosDividendos']),
      concorrentes: _listaMapasDinamicos(json['concorrentes']),
      avisos: (json['avisos'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
      ehCripto: json['ehCripto'] as bool? ?? false,
      opinioesAnalistas: json['opinioesAnalistas'] as Map<String, dynamic>?,
    );
  }

  static List<Map<String, String>> _listaMapasString(dynamic valor) {
    final lista = valor as List<dynamic>? ?? [];
    return lista.map((item) {
      final mapa = item as Map<String, dynamic>;
      return mapa.map((k, v) => MapEntry(k, v?.toString() ?? ''));
    }).toList();
  }

  static List<Map<String, dynamic>> _listaMapasDinamicos(dynamic valor) {
    final lista = valor as List<dynamic>? ?? [];
    return lista.map((item) => Map<String, dynamic>.from(item as Map)).toList();
  }
}
