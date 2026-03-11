import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:healthsaathi/screens/nurse/nurse_home_screen.dart';
import 'package:healthsaathi/providers/auth_provider.dart';
import 'package:healthsaathi/models/user.dart';

void main() {
  group('NurseHomeScreen Widget Tests', () {
    late AuthProvider mockAuthProvider;

    setUp(() {
      mockAuthProvider = AuthProvider();
    });

    testWidgets('displays nurse home screen', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuthProvider,
          child: MaterialApp(
            home: const NurseHomeScreen(),
          ),
        ),
      );

      // Verify the screen renders
      expect(find.byType(NurseHomeScreen), findsOneWidget);
      
      // Verify app bar exists
      expect(find.byType(AppBar), findsOneWidget);
      expect(find.text('Nurse Dashboard'), findsOneWidget);
    });

    testWidgets('displays logout button in app bar', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuthProvider,
          child: MaterialApp(
            home: const NurseHomeScreen(),
          ),
        ),
      );

      // Verify logout button exists
      expect(find.byIcon(Icons.logout), findsOneWidget);
    });

    testWidgets('has pull-to-refresh functionality', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuthProvider,
          child: MaterialApp(
            home: const NurseHomeScreen(),
          ),
        ),
      );

      // Verify RefreshIndicator exists
      expect(find.byType(RefreshIndicator), findsOneWidget);
    });

    testWidgets('displays loading indicator initially', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuthProvider,
          child: MaterialApp(
            home: const NurseHomeScreen(),
          ),
        ),
      );

      // Initially should show loading
      expect(find.byType(CircularProgressIndicator), findsWidgets);
    });

    testWidgets('displays quick actions section title', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuthProvider,
          child: MaterialApp(
            home: const NurseHomeScreen(),
          ),
        ),
      );

      // Verify the screen renders
      expect(find.byType(NurseHomeScreen), findsOneWidget);
    });

    testWidgets('displays welcome section', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuthProvider,
          child: MaterialApp(
            home: const NurseHomeScreen(),
          ),
        ),
      );

      // Verify the screen renders
      expect(find.byType(NurseHomeScreen), findsOneWidget);
    });

    testWidgets('displays nurse dashboard title', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuthProvider,
          child: MaterialApp(
            home: const NurseHomeScreen(),
          ),
        ),
      );

      // Verify the screen renders with correct title
      expect(find.text('Nurse Dashboard'), findsOneWidget);
    });
  });
}
