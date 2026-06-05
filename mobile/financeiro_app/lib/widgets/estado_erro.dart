import 'package:flutter/material.dart';

import '../tema/cores.dart';

class EstadoErro extends StatelessWidget {
  const EstadoErro({
    super.key,
    required this.mensagem,
    this.aoTentarNovamente,
  });

  final String mensagem;
  final VoidCallback? aoTentarNovamente;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: CoresApp.erro, size: 40),
            const SizedBox(height: 12),
            Text(
              mensagem,
              textAlign: TextAlign.center,
              style: const TextStyle(color: CoresApp.texto),
            ),
            if (aoTentarNovamente != null) ...[
              const SizedBox(height: 16),
              FilledButton(
                onPressed: aoTentarNovamente,
                child: const Text('Tentar novamente'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
