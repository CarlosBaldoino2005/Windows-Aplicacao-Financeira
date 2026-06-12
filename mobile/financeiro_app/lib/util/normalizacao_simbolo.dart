import '../dados/universo_mercado.dart';

/// Normaliza e valida simbolos de ativos (espelha validadores Python).
class NormalizacaoSimbolo {
  static final RegExp _padraoSimbolo = RegExp(r'^[A-Za-z0-9.\-^]{1,20}$');

  static const Map<String, String> _aliasesCripto = {
    'BITCOIN': 'BTC-USD',
    'BTC': 'BTC-USD',
    'ETHEREUM': 'ETH-USD',
    'ETH': 'ETH-USD',
    'SOLANA': 'SOL-USD',
    'SOL': 'SOL-USD',
    'DOGECOIN': 'DOGE-USD',
    'DOGE': 'DOGE-USD',
    'RIPPLE': 'XRP-USD',
    'XRP': 'XRP-USD',
    'CARDANO': 'ADA-USD',
    'ADA': 'ADA-USD',
    'POLYGON': 'POL-USD',
    'MATIC': 'MATIC-USD',
    'POL': 'POL-USD',
  };

  static bool ehAcaoB3(String simbolo) => simbolo.toUpperCase().endsWith('.SA');

  static String codigoBrapi(String simbolo) => simbolo.toUpperCase().replaceAll('.SA', '');

  static ({String? simbolo, String? erro}) normalizarAcao(String simbolo) {
    final limpo = simbolo.trim().toUpperCase();
    if (limpo.isEmpty) {
      return (simbolo: null, erro: 'Informe o codigo do ativo.');
    }
    if (!_padraoSimbolo.hasMatch(limpo)) {
      return (simbolo: null, erro: 'Codigo invalido.');
    }
    if (limpo.endsWith('.SA')) return (simbolo: limpo, erro: null);
    if (RegExp(r'^[A-Z]{3,5}\d{1,2}$').hasMatch(limpo)) {
      return (simbolo: '$limpo.SA', erro: null);
    }
    if (RegExp(r'^[A-Z]{1,5}$').hasMatch(limpo)) {
      return (simbolo: limpo, erro: null);
    }
    if (limpo.startsWith('^')) return (simbolo: limpo, erro: null);
    return (simbolo: null, erro: 'Formato de ticker nao reconhecido.');
  }

  static ({String? simbolo, String? erro}) normalizarCripto(String simbolo) {
    if (simbolo.trim().isEmpty) {
      return (simbolo: null, erro: 'Informe o codigo da cripto (ex.: BTC ou ETH-USD).');
    }
    var limpo = simbolo.trim().toUpperCase().replaceAll('/', '-').replaceAll(' ', '');
    if (!_padraoSimbolo.hasMatch(limpo)) {
      return (simbolo: null, erro: 'Codigo invalido. Use letras, numeros e hifen.');
    }
    if (_aliasesCripto.containsKey(limpo)) {
      return (simbolo: _aliasesCripto[limpo], erro: null);
    }
    if (limpo.contains('-USD') || limpo.contains('-USDT')) {
      return (simbolo: limpo, erro: null);
    }
    if (RegExp(r'^[A-Z0-9]{2,12}$').hasMatch(limpo)) {
      return (simbolo: '$limpo-USD', erro: null);
    }
    return (simbolo: null, erro: 'Codigo de cripto nao reconhecido.');
  }

  static String? normalizarIndice(String simbolo) {
    final limpo = simbolo.trim().toUpperCase();
    final validos = UniversoMercado.indices.map((i) => i.simbolo).toSet();
    if (validos.contains(limpo)) return limpo;
    final acao = normalizarAcao(simbolo);
    if (acao.erro == null && acao.simbolo != null && validos.contains(acao.simbolo)) {
      return acao.simbolo;
    }
    return null;
  }

  static bool ehFii(String simbolo) {
    final limpo = simbolo.trim().toUpperCase();
    if (!limpo.endsWith('.SA')) return false;
    if (UniversoMercado.fiisB3.contains(codigoBrapi(limpo))) return true;
    final codigo = codigoBrapi(limpo);
    if (!codigo.endsWith('11')) return false;
    if (UniversoMercado.unidadesNaoFii.contains(codigo)) return false;
    final prefixo = codigo.substring(0, codigo.length - 2);
    return prefixo.length == 4 && RegExp(r'^[A-Z]+$').hasMatch(prefixo);
  }
}
