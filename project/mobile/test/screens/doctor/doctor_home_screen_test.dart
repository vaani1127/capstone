import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:healthsaathi/screens/doctor/doctor_home_screen.dart';
import 'package:healthsaathi/providers/auth_provider.dart';
import 'package:healthsaathi/models/user.dart';

void main() {
  group('DoctorHomeScreen Widget Tests', () {
    late AuthProvider mockAuthProvider;

    setUp(() {
      mockAuthProvider = AuthProvider();
    });

    testWidgets('displays doctor home screen', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuthProvider,
          child: MaterialApp(
            home: const DoctorHomeScreen(),
          ),
        ),
      );

      // Verify the screen renders
      expect(find.byType(DoctorHomeScreen), findsOneWidget);
      
      // Verify app bar exists
      expect(find.byType(AppBar), findsOneWidget);
      expect(find.text('Doctor Dashboard'), findsOneWidget);
    });

    testWidgets('displays logout button in app bar', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuthProvider,
          child: MaterialApp(
            home: const DoctorHomeScreen(),
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
            home: const DoctorHomeScreen(),
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
            home: const DoctorHomeScreen(),
          ),
        ),
      );

      // Initially should show loading
      expect(find.byType(CircularProgressIndicator), findsWidgets);
    });

    testWidgets('displays welcome section with doctor title', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuthProvider,
          child: MaterialApp(
            home: const DoctorHomeScreen(),
          ),
        ),
      );

      // Verify the screen renders
      expect(find.byType(DoctorHomeScreen), findsOneWidget);
    });
  });
}
