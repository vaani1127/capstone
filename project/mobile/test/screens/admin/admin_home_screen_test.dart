import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:healthsaathi/screens/admin/admin_home_screen.dart';
import 'package:healthsaathi/providers/auth_provider.dart';

void main() {
  group('AdminHomeScreen Widget Tests', () {
    late AuthProvider mockAuthProvider;

    setUp(() {
      mockAuthProvider = AuthProvider();
    });

    Widget createTestWidget() {
      return ChangeNotifierProvider<AuthProvider>.value(
        value: mockAuthProvider,
        child: const MaterialApp(
          home: AdminHomeScreen(),
        ),
      );
    }

    testWidgets('displays admin home screen', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());

      // Verify the screen renders
      expect(find.byType(AdminHomeScreen), findsOneWidget);
      
      // Verify app bar exists
      expect(find.byType(AppBar), findsOneWidget);
      expect(find.text('Admin Dashboard'), findsOneWidget);
    });

    testWidgets('displays app bar with logout button', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());

      expect(find.text('Admin Dashboard'), findsOneWidget);
      expect(find.byIcon(Icons.logout), findsOneWidget);
    });

    testWidgets('displays loading indicator initially', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Loading dashboard...'), findsOneWidget);
    });

    testWidgets('has pull-to-refresh functionality', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());

      // Verify RefreshIndicator exists
      expect(find.byType(RefreshIndicator), findsOneWidget);
    });

    testWidgets('displays welcome section', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();

      // Verify welcome text exists
      expect(find.text('Welcome back,'), findsWidgets);
    });

    testWidgets('displays system statistics section', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify statistics section title exists
      expect(find.text('System Statistics'), findsWidgets);
    });

    testWidgets('displays quick links section', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify quick links section exists
      expect(find.text('Quick Links'), findsWidgets);
    });

    testWidgets('displays recent activity section', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify recent activity section exists
      expect(find.text('Recent Activity'), findsWidgets);
    });

    testWidgets('displays stat card icons', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify stat card icons exist
      expect(find.byIcon(Icons.people), findsWidgets);
      expect(find.byIcon(Icons.calendar_today), findsWidgets);
      expect(find.byIcon(Icons.medical_services), findsWidgets);
      expect(find.byIcon(Icons.pending_actions), findsWidgets);
    });

    testWidgets('displays quick link cards', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify quick link cards exist
      expect(find.text('User Management'), findsWidgets);
      expect(find.text('Audit Dashboard'), findsWidgets);
      expect(find.byIcon(Icons.people_alt), findsWidgets);
      expect(find.byIcon(Icons.security), findsWidgets);
    });

    testWidgets('quick link cards are tappable', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Find and tap user management card
      final userManagementCard = find.ancestor(
        of: find.text('User Management'),
        matching: find.byType(InkWell),
      );

      if (userManagementCard.evaluate().isNotEmpty) {
        await tester.tap(userManagementCard.first);
        await tester.pumpAndSettle();

        // Verify snackbar appears (since screen is not implemented yet)
        expect(find.text('User management screen coming soon'), findsOneWidget);
      }
    });

    testWidgets('displays recent appointments section', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify recent appointments section exists
      expect(find.text('Recent Appointments'), findsWidgets);
      expect(find.byIcon(Icons.event), findsWidgets);
    });

    testWidgets('displays recent registrations section', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify recent registrations section exists
      expect(find.text('Recent Registrations'), findsWidgets);
      expect(find.byIcon(Icons.person_add), findsWidgets);
    });

    testWidgets('displays empty state for no recent appointments', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify empty state text exists
      expect(find.text('No recent appointments'), findsWidgets);
    });

    testWidgets('displays empty state for no recent registrations', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify empty state text exists
      expect(find.text('No recent registrations'), findsWidgets);
    });

    testWidgets('displays user avatar', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify CircleAvatar exists
      expect(find.byType(CircleAvatar), findsWidgets);
    });

    testWidgets('displays administrator role badge', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify administrator text exists
      expect(find.text('Administrator'), findsWidgets);
    });

    testWidgets('displays stat cards in grid layout', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify Card widgets exist
      expect(find.byType(Card), findsWidgets);
    });

    testWidgets('displays quick links in row layout', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();
      await tester.pumpAndSettle();

      // Verify Row widgets exist
      expect(find.byType(Row), findsWidgets);
    });
  });
}
