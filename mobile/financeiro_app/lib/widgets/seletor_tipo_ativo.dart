import 'package:flutter/material.dart';

import '../modelos/tipo_ativo.dart';

/// Barra horizontal para escolher o tipo de ativo (Ações, Cripto, FIIs, Índices).
class SeletorTipoAtivo extends StatelessWidget {
  const SeletorTipoAtivo({
    super.key,
    required this.tipoSelecionado,
    required this.aoMudar,
  });

  final TipoAtivo tipoSelecionado;
  final ValueChanged<TipoAtivo> aoMudar;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: TipoAtivo.values.map((tipo) {
          final selecionado = tipo == tipoSelecionado;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: Text(tipo.rotulo),
              selected: selecionado,
              onSelected: (_) => aoMudar(tipo),
            ),
          );
        }).toList(),
      ),
    );
  }
}
