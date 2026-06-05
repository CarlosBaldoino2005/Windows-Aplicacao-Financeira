import 'package:flutter/material.dart';

/// Tokens do modelo-ui (modo claro).
class CoresApp {
  static const Color primaria = Color(0xFF2563EB);
  static const Color primariaHover = Color(0xFF1D4ED8);
  static const Color fundo = Color(0xFFF8FAFC);
  static const Color superficie = Color(0xFFFFFFFF);
  static const Color borda = Color(0xFFE2E8F0);
  static const Color texto = Color(0xFF0F172A);
  static const Color textoSecundario = Color(0xFF64748B);
  static const Color sucesso = Color(0xFF16A34A);
  static const Color erro = Color(0xFFDC2626);

  static ThemeData temaClaro() {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaria,
        surface: superficie,
      ),
      scaffoldBackgroundColor: fundo,
      appBarTheme: const AppBarTheme(
        backgroundColor: superficie,
        foregroundColor: texto,
        elevation: 0,
        centerTitle: false,
      ),
      cardTheme: CardThemeData(
        color: superficie,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: borda),
        ),
      ),
      tabBarTheme: const TabBarThemeData(
        labelColor: primaria,
        unselectedLabelColor: textoSecundario,
        indicatorColor: primaria,
      ),
    );
  }
}
