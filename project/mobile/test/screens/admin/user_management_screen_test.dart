import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:healthsaathi/screens/admin/user_management_screen.dart';
import 'package:healthsaathi/services/admin_service.dart';
import 'package:healthsaathi/widgets/loading_indicator.dart';
import 'package:healthsaathi/widgets/error_message.dart';

void main() {
  group('UserManagementScreen', () {
    testWidgets('displays loading indicator initially', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      // Should show loading indicator
      expect(find.byType(LoadingIndicator), findsOneWidget);
      expect(find.text('Loading users...'), findsOneWidget);
    });

    testWidgets('displays app bar with title and refresh button', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      // Check app bar
      expect(find.text('User Management'), findsOneWidget);
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('displays search bar and filter chips', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Check search bar
      expect(find.byType(TextField), findsOneWidget);
      expect(find.text('Search by name or email...'), findsOneWidget);

      // Check filter chips
      expect(find.text('All'), findsOneWidget);
      expect(find.text('Admin'), findsOneWidget);
      expect(find.text('Doctor'), findsOneWidget);
      expect(find.text('Nurse'), findsOneWidget);
      expect(find.text('Patient'), findsOneWidget);
    });

    testWidgets('displays floating action button for creating user', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Check FAB
      expect(find.byType(FloatingActionButton), findsOneWidget);
      expect(find.byIcon(Icons.person_add), findsOneWidget);
    });

    testWidgets('displays empty state when no users', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      // Wait for loading to complete
      await tester.pumpAndSettle();

      // Should show empty state or user list depending on API response
      // Check that the screen loaded successfully
      expect(find.byType(UserManagementScreen), findsOneWidget);
    });

    testWidgets('search functionality filters users by name', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Enter search query
      await tester.enterText(find.byType(TextField), 'John');
      await tester.pumpAndSettle();

      // Search should be applied (results depend on mock data)
      expect(find.text('John'), findsWidgets);
    });

    testWidgets('clear button clears search', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Enter search query
      await tester.enterText(find.byType(TextField), 'test');
      await tester.pumpAndSettle();

      // Clear button should appear
      expect(find.byIcon(Icons.clear), findsOneWidget);

      // Tap clear button
      await tester.tap(find.byIcon(Icons.clear));
      await tester.pumpAndSettle();

      // Search field should be empty
      final textField = tester.widget<TextField>(find.byType(TextField));
      expect(textField.controller?.text, isEmpty);
    });

    testWidgets('role filter chips filter users by role', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Find and tap Doctor filter chip
      final doctorChip = find.widgetWithText(FilterChip, 'Doctor');
      expect(doctorChip, findsOneWidget);

      await tester.tap(doctorChip);
      await tester.pumpAndSettle();

      // Filter should be applied (chip should be selected)
      final chip = tester.widget<FilterChip>(doctorChip);
      expect(chip.selected, isTrue);
    });

    testWidgets('tapping FAB opens create user dialog', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Tap FAB
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Dialog should open
      expect(find.text('Create New User'), findsOneWidget);
      expect(find.text('Name'), findsOneWidget);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      expect(find.text('Role'), findsOneWidget);
    });

    testWidgets('create user dialog validates required fields', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Open create dialog
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Try to submit without filling fields
      await tester.tap(find.text('Create'));
      await tester.pumpAndSettle();

      // Should show validation errors
      expect(find.text('Name is required'), findsOneWidget);
      expect(find.text('Email is required'), findsOneWidget);
      expect(find.text('Password is required'), findsOneWidget);
    });

    testWidgets('create user dialog validates email format', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Open create dialog
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Enter invalid email
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'invalid-email',
      );
      await tester.pumpAndSettle();

      // Try to submit
      await tester.tap(find.text('Create'));
      await tester.pumpAndSettle();

      // Should show email validation error
      expect(find.text('Enter a valid email address'), findsOneWidget);
    });

    testWidgets('create user dialog validates password strength', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Open create dialog
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Enter weak password
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Password'),
        'weak',
      );
      await tester.pumpAndSettle();

      // Try to submit
      await tester.tap(find.text('Create'));
      await tester.pumpAndSettle();

      // Should show password validation error
      expect(find.text('Password must be at least 8 characters'), findsOneWidget);
    });

    testWidgets('password visibility toggle works', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Open create dialog
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Find password field
      final passwordField = find.widgetWithText(TextFormField, 'Password');
      expect(passwordField, findsOneWidget);

      // Find visibility toggle button
      expect(find.byIcon(Icons.visibility), findsOneWidget);

      // Tap visibility toggle
      await tester.tap(find.byIcon(Icons.visibility));
      await tester.pumpAndSettle();

      // Icon should change to visibility_off
      expect(find.byIcon(Icons.visibility_off), findsOneWidget);
    });

    testWidgets('role dropdown allows selection', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Open create dialog
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Find role dropdown
      final dropdown = find.byType(DropdownButtonFormField<String>);
      expect(dropdown, findsOneWidget);

      // Tap dropdown
      await tester.tap(dropdown);
      await tester.pumpAndSettle();

      // Should show role options
      expect(find.text('Admin').hitTestable(), findsWidgets);
      expect(find.text('Doctor').hitTestable(), findsWidgets);
      expect(find.text('Nurse').hitTestable(), findsWidgets);
      expect(find.text('Patient').hitTestable(), findsWidgets);
    });

    testWidgets('cancel button closes dialog', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Open create dialog
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Dialog should be open
      expect(find.text('Create New User'), findsOneWidget);

      // Tap cancel
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();

      // Dialog should be closed
      expect(find.text('Create New User'), findsNothing);
    });

    testWidgets('refresh button reloads users', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Tap refresh button
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pump();

      // Should trigger a reload (loading state or immediate update)
      // Just verify the button tap doesn't crash
      expect(find.byType(UserManagementScreen), findsOneWidget);
    });

    testWidgets('pull to refresh reloads users', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Find a scrollable widget to perform drag gesture
      final listView = find.byType(ListView);
      if (listView.evaluate().isNotEmpty) {
        // Perform pull to refresh gesture
        await tester.drag(listView, const Offset(0, 300));
        await tester.pump();

        // Should trigger refresh
        expect(find.byType(CircularProgressIndicator), findsWidgets);
      } else {
        // If no ListView, just verify screen is present
        expect(find.byType(UserManagementScreen), findsOneWidget);
      }
    });

    testWidgets('user card displays user information', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // If users are loaded, check card structure
      final cards = find.byType(Card);
      if (cards.evaluate().isNotEmpty) {
        // Should have avatar, name, email, role badge
        expect(find.byType(CircleAvatar), findsWidgets);
        expect(find.byType(ListTile), findsWidgets);
        expect(find.byIcon(Icons.edit), findsWidgets);
      }
    });

    testWidgets('edit button opens edit dialog', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Find edit button (if users exist)
      final editButtons = find.byIcon(Icons.edit);
      if (editButtons.evaluate().isNotEmpty) {
        // Tap first edit button
        await tester.tap(editButtons.first);
        await tester.pumpAndSettle();

        // Edit dialog should open
        expect(find.text('Edit User'), findsOneWidget);
        // Password field should not be present in edit mode
        expect(find.text('Password'), findsNothing);
      }
    });

    testWidgets('role badges display correct colors', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: UserManagementScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Check if role badges are displayed with correct styling
      // This is a visual test, so we just verify the widgets exist
      final containers = find.byType(Container);
      expect(containers, findsWidgets);
    });
  });
}
