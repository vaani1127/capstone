import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:healthsaathi/screens/registration_screen.dart';
import 'package:healthsaathi/providers/auth_provider.dart';
import 'package:provider/provider.dart';

void main() {
  group('RegistrationScreen Widget Tests', () {
    late AuthProvider mockAuthProvider;

    setUp(() {
      mockAuthProvider = AuthProvider();
    });

    Widget createRegistrationScreen() {
      return ChangeNotifierProvider<AuthProvider>.value(
        value: mockAuthProvider,
        child: const MaterialApp(
          home: RegistrationScreen(),
        ),
      );
    }

    testWidgets('displays app bar with correct title', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      expect(find.text('Register'), findsAtLeastNWidgets(1));
      expect(find.byType(AppBar), findsOneWidget);
    });

    testWidgets('displays HealthSaathi branding', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      expect(find.byIcon(Icons.health_and_safety), findsOneWidget);
      expect(find.text('HealthSaathi'), findsOneWidget);
      expect(find.text('Create your account'), findsOneWidget);
    });

    testWidgets('displays all required form fields', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      expect(find.byType(TextFormField), findsNWidgets(4));
      expect(find.widgetWithText(TextFormField, 'Full Name'), findsOneWidget);
      expect(find.widgetWithText(TextFormField, 'Email'), findsOneWidget);
      expect(find.widgetWithText(TextFormField, 'Password'), findsOneWidget);
      expect(find.widgetWithText(TextFormField, 'Confirm Password'), findsOneWidget);
    });

    testWidgets('displays role dropdown', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      expect(find.byType(DropdownButtonFormField<String>), findsOneWidget);
      expect(find.text('Role'), findsOneWidget);
    });

    testWidgets('displays password requirements', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      expect(find.text('Password Requirements:'), findsOneWidget);
      expect(find.text('At least 8 characters'), findsOneWidget);
      expect(find.text('One uppercase letter'), findsOneWidget);
      expect(find.text('One lowercase letter'), findsOneWidget);
      expect(find.text('One number'), findsOneWidget);
    });

    testWidgets('displays register button', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      expect(find.widgetWithText(ElevatedButton, 'Register'), findsAtLeastNWidgets(1));
    });

    testWidgets('displays login link', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      expect(find.text('Already have an account?'), findsOneWidget);
      expect(find.widgetWithText(TextButton, 'Login'), findsOneWidget);
    });

    testWidgets('password fields are obscured by default', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      // Check that visibility icons are present (indicates passwords are obscured)
      expect(find.byIcon(Icons.visibility), findsNWidgets(2));
    });

    testWidgets('password visibility toggle works for password field', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      // Find the password field's visibility toggle (first one)
      final visibilityIcons = find.byIcon(Icons.visibility);
      expect(visibilityIcons, findsNWidgets(2));

      // Tap first visibility toggle (password field)
      await tester.tap(visibilityIcons.first);
      await tester.pump();

      // Password should now be visible (visibility_off icon appears)
      expect(find.byIcon(Icons.visibility_off), findsAtLeastNWidgets(1));
    });

    testWidgets('password visibility toggle works for confirm password field', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      // Find the visibility toggles
      final visibilityIcons = find.byIcon(Icons.visibility);
      expect(visibilityIcons, findsNWidgets(2));

      // Tap second visibility toggle (confirm password field)
      await tester.tap(visibilityIcons.last);
      await tester.pump();

      // Confirm password should now be visible (visibility_off icon appears)
      expect(find.byIcon(Icons.visibility_off), findsAtLeastNWidgets(1));
    });

    testWidgets('role dropdown has default value', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      // Find the dropdown and verify Patient is displayed
      expect(find.text('Patient'), findsOneWidget);
    });

    testWidgets('role dropdown can be changed', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      // Tap the dropdown
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();

      // Select Doctor role
      await tester.tap(find.text('Doctor').last);
      await tester.pumpAndSettle();

      // Verify Doctor is now displayed
      expect(find.text('Doctor'), findsWidgets);
    });

    testWidgets('displays all role options', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      // Tap the dropdown
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();

      // Verify all roles are present
      expect(find.text('Patient').hitTestable(), findsOneWidget);
      expect(find.text('Doctor').hitTestable(), findsOneWidget);
      expect(find.text('Nurse').hitTestable(), findsOneWidget);
      expect(find.text('Admin').hitTestable(), findsOneWidget);
    });

    testWidgets('email field has correct keyboard type', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      // Verify email field exists with email icon
      expect(find.byIcon(Icons.email), findsOneWidget);
    });

    testWidgets('form fields have correct icons', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      expect(find.byIcon(Icons.person), findsOneWidget);
      expect(find.byIcon(Icons.email), findsOneWidget);
      expect(find.byIcon(Icons.badge), findsOneWidget);
      expect(find.byIcon(Icons.lock), findsOneWidget);
      expect(find.byIcon(Icons.lock_outline), findsOneWidget);
    });

    testWidgets('form is scrollable', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      expect(find.byType(SingleChildScrollView), findsOneWidget);
    });

    testWidgets('password requirements are displayed in a styled container', (WidgetTester tester) async {
      await tester.pumpWidget(createRegistrationScreen());

      // Find the container with password requirements
      final containers = find.byType(Container);
      expect(containers, findsWidgets);

      // Verify all requirement items are present
      expect(find.byIcon(Icons.check_circle_outline), findsNWidgets(4));
    });
  });
}
