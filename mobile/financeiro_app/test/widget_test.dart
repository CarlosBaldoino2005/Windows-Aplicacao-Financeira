// Teste basico do app Financeiro (splash / MaterialApp).

import 'package:flutter_test/flutter_test.dart';

import 'package:financeiro_app/main.dart';

void main() {
  testWidgets('FinanceiroApp monta sem erro', (WidgetTester tester) async {
    await tester.pumpWidget(const FinanceiroApp());
    expect(find.byType(FinanceiroApp), findsOneWidget);
  });
}
