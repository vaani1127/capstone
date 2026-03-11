import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:healthsaathi/screens/patient/medical_history_screen.dart';

void main() {
  group('MedicalHistoryScreen', () {
    Widget createTestWidget() {
      return const MaterialApp(
        home: MedicalHistoryScreen(),
      );
    }

    testWidgets('displays app bar with title', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      
      expect(find.text('Medical History'), findsOneWidget);
      expect(find.byIcon(Icons.filter_list), findsOneWidget);
    });

    testWidgets('displays loading indicator initially', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Loading medical records...'), findsOneWidget);
    });

    testWidgets('has refresh indicator', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      
      expect(find.byType(RefreshIndicator), findsOneWidget);
    });
  });
}
