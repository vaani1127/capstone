import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:healthsaathi/screens/admin/audit_dashboard_screen.dart';

void main() {
  group('AuditDashboardScreen Widget Tests', () {
    testWidgets('displays app bar with title and actions', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AuditDashboardScreen(),
        ),
      );

      // Wait for initial load
      await tester.pump();

      // Verify app bar title
      expect(find.text('Audit Dashboard'), findsOneWidget);
      
      // Verify export button
      expect(find.byIcon(Icons.download), findsOneWidget);
      
      // Verify refresh button
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('displays loading indicator initially', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AuditDashboardScreen(),
        ),
      );

      // Should show loading indicator
      expect(find.text('Loading audit data...'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('export menu shows JSON and CSV options', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AuditDashboardScreen(),
        ),
      );

      // Wait for initial load
      await tester.pump();

      // Tap export button
      await tester.tap(find.byIcon(Icons.download));
      await tester.pumpAndSettle();

      // Verify export options
      expect(find.text('Export as JSON'), findsOneWidget);
      expect(find.text('Export as CSV'), findsOneWidget);
    });

    testWidgets('refresh button is present and tappable', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AuditDashboardScreen(),
        ),
      );

      // Wait for initial load
      await tester.pump();

      // Find refresh button
      final refreshButton = find.byIcon(Icons.refresh);
      expect(refreshButton, findsOneWidget);
      
      // Tap refresh button
      await tester.tap(refreshButton);
      await tester.pump();

      // Verify the screen is still functional (doesn't crash)
      expect(find.byType(AuditDashboardScreen), findsOneWidget);
    });

    testWidgets('screen has RefreshIndicator for pull to refresh', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AuditDashboardScreen(),
        ),
      );

      // Wait for initial load
      await tester.pump();

      // Verify RefreshIndicator exists
      expect(find.byType(RefreshIndicator), findsOneWidget);
    });

    testWidgets('screen structure is correct', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AuditDashboardScreen(),
        ),
      );

      // Verify basic structure
      expect(find.byType(Scaffold), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
      expect(find.byType(AuditDashboardScreen), findsOneWidget);
    });

    testWidgets('export button opens popup menu', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AuditDashboardScreen(),
        ),
      );

      await tester.pump();

      // Find export button
      final exportButton = find.byIcon(Icons.download);
      expect(exportButton, findsOneWidget);

      // Tap to open menu
      await tester.tap(exportButton);
      await tester.pumpAndSettle();

      // Verify popup menu items
      expect(find.byType(PopupMenuItem<String>), findsNWidgets(2));
    });

    testWidgets('app bar has correct title', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AuditDashboardScreen(),
        ),
      );

      await tester.pump();

      // Verify title
      final titleFinder = find.descendant(
        of: find.byType(AppBar),
        matching: find.text('Audit Dashboard'),
      );
      expect(titleFinder, findsOneWidget);
    });

    testWidgets('screen renders without errors', (WidgetTester tester) async {
      // This test verifies the screen can be instantiated and rendered
      await tester.pumpWidget(
        const MaterialApp(
          home: AuditDashboardScreen(),
        ),
      );

      await tester.pump();

      // No exceptions should be thrown
      expect(find.byType(AuditDashboardScreen), findsOneWidget);
    });

    testWidgets('loading state shows progress indicator', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AuditDashboardScreen(),
        ),
      );

      // In loading state
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Loading audit data...'), findsOneWidget);
    });
  });
}

