import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:healthsaathi/screens/patient/queue_status_screen.dart';

void main() {
  group('QueueStatusScreen Widget Tests', () {
    testWidgets('displays queue status screen', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: QueueStatusScreen(
            doctorId: 1,
            doctorName: 'Dr. Smith',
          ),
        ),
      );

      // Verify the screen renders
      expect(find.byType(QueueStatusScreen), findsOneWidget);
      
      // Verify app bar exists with doctor name
      expect(find.byType(AppBar), findsOneWidget);
      expect(find.text('Dr. Smith'), findsOneWidget);
    });

    testWidgets('displays refresh button in app bar', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: QueueStatusScreen(
            doctorId: 1,
            doctorName: 'Dr. Smith',
          ),
        ),
      );

      // Verify refresh button exists
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('has pull-to-refresh functionality', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: QueueStatusScreen(
            doctorId: 1,
            doctorName: 'Dr. Smith',
          ),
        ),
      );

      // Verify RefreshIndicator exists
      expect(find.byType(RefreshIndicator), findsOneWidget);
    });

    testWidgets('displays loading indicator initially', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: QueueStatusScreen(
            doctorId: 1,
            doctorName: 'Dr. Smith',
          ),
        ),
      );

      // Initially should show loading
      expect(find.byType(CircularProgressIndicator), findsWidgets);
      expect(find.text('Loading queue status...'), findsOneWidget);
    });

    testWidgets('uses doctor name in title when provided', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: QueueStatusScreen(
            doctorId: 1,
            doctorName: 'Dr. John Doe',
          ),
        ),
      );

      // Verify doctor name is displayed in app bar
      expect(find.text('Dr. John Doe'), findsOneWidget);
    });

    testWidgets('uses default title when doctor name not provided', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: QueueStatusScreen(
            doctorId: 1,
          ),
        ),
      );

      // Verify default title is displayed
      expect(find.text('Queue Status'), findsOneWidget);
    });
  });
}
