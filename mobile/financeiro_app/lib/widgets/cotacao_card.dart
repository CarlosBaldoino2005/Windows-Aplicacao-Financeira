import 'package:flutter/material.dart';

import '../modelos/cotacao_resumo.dart';
import '../tema/cores.dart';
import '../util/formatadores.dart';

class CotacaoCard extends StatelessWidget {
  const CotacaoCard({
    super.key,
    required this.cotacao,
    this.ehFavorito = false,
    this.aoAlternarFavorito,
    this.aoTocar,
  });

  final CotacaoResumo cotacao;
  final bool ehFavorito;
  final VoidCallback? aoAlternarFavorito;
  final VoidCallback? aoTocar;

  @override
  Widget build(BuildContext context) {
    final subiu = cotacao.variacaoPercentual >= 0;
    final corVariacao = subiu ? CoresApp.sucesso : CoresApp.erro;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: aoTocar,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      cotacao.codigo,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: CoresApp.texto,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      cotacao.nome,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        color: CoresApp.textoSecundario,
                      ),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    formatarMoeda(cotacao.preco, cotacao.moeda),
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                  Text(
                    formatarVariacao(cotacao.variacaoPercentual),
                    style: TextStyle(color: corVariacao, fontWeight: FontWeight.w600),
                  ),
                ],
              ),
              if (aoAlternarFavorito != null) ...[
                const SizedBox(width: 4),
                IconButton(
                  onPressed: aoAlternarFavorito,
                  icon: Icon(
                    ehFavorito ? Icons.star : Icons.star_border,
                    color: ehFavorito ? Colors.amber : CoresApp.textoSecundario,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
