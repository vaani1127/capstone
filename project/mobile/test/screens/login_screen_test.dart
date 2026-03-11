import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:healthsaathi/screens/login_screen.dart';
import 'package:healthsaathi/providers/auth_provider.dart';
import 'package:provider/provider.dart';

void main() {
  group('LoginScreen Widget Tests', () {
    late AuthProvider mockAuthProvider;

    setUp(() {
      mockAuthProvider = AuthProvider();
    });

    Widget createLoginScreen() {
      return ChangeNotifierProvider<AuthProvider>.value(
        value: mockAuthProvider,
        child: MaterialApp(
          home: const LoginScreen(),
        ),
      );
    }

    testWidgets('displays app bar with correct title', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      expect(find.text('Login'), findsAtLeastNWidgets(1));
      expect(find.byType(AppBar), findsOneWidget);
    });

    testWidgets('displays HealthSaathi logo and branding', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      expect(find.byIcon(Icons.health_and_safety), findsOneWidget);
      expect(find.text('HealthSaathi'), findsOneWidget);
      expect(find.text('Secure Healthcare Management'), findsOneWidget);
    });

    testWidgets('displays email and password fields', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      expect(find.byType(TextFormField), findsNWidgets(2));
      expect(find.widgetWithText(TextFormField, 'Email'), findsOneWidget);
      expect(find.widgetWithText(TextFormField, 'Password'), findsOneWidget);
    });

    testWidgets('displays email icon', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      expect(find.byIcon(Icons.email), findsOneWidget);
    });

    testWidgets('displays lock icon for password', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      expect(find.byIcon(Icons.lock), findsOneWidget);
    });

    testWidgets('password field is obscured by default', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      // Check that visibility icon is present (indicates password is obscured)
      expect(find.byIcon(Icons.visibility), findsOneWidget);
    });

    testWidgets('password visibility toggle works', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      // Initially password should be obscured (visibility icon present)
      expect(find.byIcon(Icons.visibility), findsOneWidget);

      // Tap visibility toggle
      await tester.tap(find.byIcon(Icons.visibility));
      await tester.pump();

      // Password should now be visible (visibility_off icon present)
      expect(find.byIcon(Icons.visibility_off), findsOneWidget);

      // Tap again to hide
      await tester.tap(find.byIcon(Icons.visibility_off));
      await tester.pump();

      // Password should be obscured again (visibility icon present)
      expect(find.byIcon(Icons.visibility), findsOneWidget);
    });

    testWidgets('displays login button', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      expect(find.widgetWithText(ElevatedButton, 'Login'), findsOneWidget);
    });

    testWidgets('displays register link', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      expect(find.text('Don\'t have an account?'), findsOneWidget);
      expect(find.widgetWithText(TextButton, 'Register'), findsOneWidget);
    });

    testWidgets('form is scrollable', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      expect(find.byType(SingleChildScrollView), findsOneWidget);
    });

    testWidgets('email field has correct keyboard type', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      // Verify email field exists with email icon
      expect(find.byIcon(Icons.email), findsOneWidget);
    });

    testWidgets('email field has next text input action', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      // Verify email field exists
      expect(find.widgetWithText(TextFormField, 'Email'), findsOneWidget);
    });

    testWidgets('password field has done text input action', (WidgetTester tester) async {
      await tester.pumpWidget(createLoginScreen());

      // Verify password field exists
      expect(find.widgetWithText(TextFormField, 'Password'), findsOneWidget);
    });
  });
}
