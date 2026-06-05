import 'package:flutter/material.dart';

import '../tema/cores.dart';

class EstadoCarregando extends StatelessWidget {
  const EstadoCarregando({super.key, this.mensagem = 'Carregando...'});

  final String mensagem;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(color: CoresApp.primaria),
          const SizedBox(height: 12),
          Text(mensagem, style: const TextStyle(color: CoresApp.textoSecundario)),
        ],
      ),
    );
  }
}
