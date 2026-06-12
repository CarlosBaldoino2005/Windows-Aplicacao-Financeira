import '../dados/universo_mercado.dart';
import '../modelos/resultado_busca.dart';
import '../modelos/tipo_ativo.dart';
import '../util/normalizacao_simbolo.dart';
import '../util/texto_busca_helper.dart';
import 'provedores/yahoo_busca_provedor.dart';

/// Busca de ativos por tipo (local + Yahoo Search).
class BuscaMercadoServico {
  BuscaMercadoServico({YahooBuscaProvedor? yahooBusca})
      : _yahooBusca = yahooBusca ?? YahooBuscaProvedor();

  final YahooBuscaProvedor _yahooBusca;

  Future<List<ResultadoBusca>> buscar(String termo, TipoAtivo tipo, {int limite = 12}) async {
    if (tipo == TipoAtivo.indices) {
      throw Exception('Use o painel Indices para consultar indices de mercado.');
    }

    final termoLimpo = termo.trim();
    if (normalizarTextoBusca(termoLimpo).length < 2) {
      throw Exception('Digite ao menos 2 caracteres para pesquisar.');
    }

    final agregado = <String, ResultadoBusca>{};
    for (final item in _buscarLocal(termoLimpo, tipo)) {
      agregado[item.simbolo] = item;
    }

    try {
      final online = await _buscarOnline(termoLimpo, tipo, limite);
      for (final item in online) {
        agregado[item.simbolo] = item;
      }
    } catch (_) {
      // Mantem resultados locais se a busca online falhar.
    }

    final lista = agregado.values.toList();
    if (tipo == TipoAtivo.acoes) {
      lista.sort((a, b) {
        final pa = a.bolsa == 'B3' ? 0 : 1;
        final pb = b.bolsa == 'B3' ? 0 : 1;
        if (pa != pb) return pa.compareTo(pb);
        return a.simbolo.compareTo(b.simbolo);
      });
    }
    return lista.take(limite).toList();
  }

  List<ResultadoBusca> _buscarLocal(String termo, TipoAtivo tipo) {
    switch (tipo) {
      case TipoAtivo.cripto:
        return _buscarCriptoLocal(termo);
      case TipoAtivo.fiis:
        return _buscarFiisLocal(termo);
      case TipoAtivo.acoes:
        return _buscarAcoesLocal(termo);
      case TipoAtivo.indices:
        return [];
    }
  }

  Future<List<ResultadoBusca>> _buscarOnline(String termo, TipoAtivo tipo, int limite) {
    switch (tipo) {
      case TipoAtivo.cripto:
        return _yahooBusca.buscarCripto(termo, limite);
      case TipoAtivo.fiis:
        return _yahooBusca.buscarAcoes(termo, limite).then((lista) {
          return lista.where((r) => NormalizacaoSimbolo.ehFii(r.simbolo)).toList();
        });
      case TipoAtivo.acoes:
        return _yahooBusca.buscarAcoes(termo, limite);
      case TipoAtivo.indices:
        return Future.value([]);
    }
  }

  List<ResultadoBusca> _buscarAcoesLocal(String termo) {
    final encontrados = <ResultadoBusca>[];
    final vistos = <String>{};
    final candidatos = [...UniversoMercado.acoesB3, ...UniversoMercado.acoesEua];

    for (final codigo in candidatos) {
      final codigoSemSufixo = codigo.replaceAll(RegExp(r'\d'), '');
      if (!textoContemBusca(termo, [codigo, codigoSemSufixo])) continue;
      final ok = NormalizacaoSimbolo.normalizarAcao(codigo);
      if (ok.erro != null || ok.simbolo == null || !vistos.add(ok.simbolo!)) continue;
      final bolsa = ok.simbolo!.endsWith('.SA') ? 'B3' : 'EUA';
      encontrados.add(ResultadoBusca(
        simbolo: ok.simbolo!,
        codigo: ok.simbolo!.replaceAll('.SA', ''),
        nome: codigo,
        bolsa: bolsa,
      ));
    }
    return encontrados;
  }

  List<ResultadoBusca> _buscarCriptoLocal(String termo) {
    final encontrados = <ResultadoBusca>[];
    final vistos = <String>{};
    for (final simbolo in UniversoMercado.criptomoedas) {
      final codigo = simbolo.replaceAll('-USD', '');
      final nome = UniversoMercado.nomesCripto[simbolo] ?? codigo;
      if (!textoContemBusca(termo, [simbolo, codigo, nome])) continue;
      final ok = NormalizacaoSimbolo.normalizarCripto(simbolo);
      if (ok.erro != null || ok.simbolo == null || !vistos.add(ok.simbolo!)) continue;
      encontrados.add(ResultadoBusca(
        simbolo: ok.simbolo!,
        codigo: ok.simbolo!.replaceAll('-USD', ''),
        nome: nome,
        bolsa: 'Cripto',
      ));
    }
    return encontrados;
  }

  List<ResultadoBusca> _buscarFiisLocal(String termo) {
    final encontrados = <ResultadoBusca>[];
    final vistos = <String>{};
    for (final codigo in UniversoMercado.fiisB3) {
      if (!textoContemBusca(termo, [codigo])) continue;
      final simbolo = '$codigo.SA';
      if (!vistos.add(simbolo)) continue;
      encontrados.add(ResultadoBusca(
        simbolo: simbolo,
        codigo: codigo,
        nome: codigo,
        bolsa: 'B3',
      ));
    }
    return encontrados;
  }
}
