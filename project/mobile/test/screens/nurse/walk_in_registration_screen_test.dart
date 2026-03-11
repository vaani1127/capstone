import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:healthsaathi/screens/nurse/walk_in_registration_screen.dart';
import 'package:healthsaathi/models/doctor.dart';
import 'package:healthsaathi/models/appointment.dart';
import 'package:healthsaathi/services/appointment_service.dart';

void main() {
  group('WalkInRegistrationScreen', () {
    testWidgets('displays loading indicator while loading doctors', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: WalkInRegistrationScreen(),
        ),
      );

      // Should show loading indicator initially
      expect(find.text('Loading doctors...'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('displays form fields after doctors are loaded', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: WalkInRegistrationScreen(),
        ),
      );

      // Wait for loading to complete
      await tester.pumpAndSettle();

      // Check for form fields
      expect(find.text('Patient Information'), findsOneWidget);
      expect(find.text('Full Name *'), findsOneWidget);
      expect(find.text('Email (Optional)'), findsOneWidget);
      expect(find.text('Phone Number (Optional)'), findsOneWidget);
      expect(find.text('Date of Birth (Optional)'), findsOneWidget);
      expect(find.text('Gender (Optional)'), findsOneWidget);
      expect(find.text('Blood Group (Optional)'), findsOneWidget);
      expect(find.text('Address (Optional)'), findsOneWidget);
      expect(find.text('Doctor Selection'), findsOneWidget);
    });

    testWidgets('validates required fields', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: WalkInRegistrationScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Try to submit without filling required fields
      final submitButton = find.text('Register Walk-in Patient');
      await tester.tap(submitButton);
      await tester.pumpAndSettle();

      // Should show validation error for name
      expect(find.text('Please enter patient name'), findsOneWidget);
    });

    testWidgets('validates email format', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: WalkInRegistrationScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Enter invalid email
      final emailField = find.widgetWithText(TextFormField, 'Email (Optional)');
      await tester.enterText(emailField, 'invalid-email');
      
      // Try to submit
      final submitButton = find.text('Register Walk-in Patient');
      await tester.tap(submitButton);
      await tester.pumpAndSettle();

      // Should show email validation error
      expect(find.text('Please enter a valid email'), findsOneWidget);
    });

    testWidgets('allows selecting gender from dropdown', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: WalkInRegistrationScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Find and tap gender dropdown
      final genderDropdown = find.widgetWithText(DropdownButtonFormField<String>, 'Gender (Optional)');
      await tester.tap(genderDropdown);
      await tester.pumpAndSettle();

      // Select 'Male'
      await tester.tap(find.text('Male').last);
      await tester.pumpAndSettle();

      // Verify selection
      expect(find.text('Male'), findsWidgets);
    });

    testWidgets('allows selecting blood group from dropdown', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: WalkInRegistrationScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Find and tap blood group dropdown
      final bloodGroupDropdown = find.widgetWithText(DropdownButtonFormField<String>, 'Blood Group (Optional)');
      await tester.tap(bloodGroupDropdown);
      await tester.pumpAndSettle();

      // Select 'O+'
      await tester.tap(find.text('O+').last);
      await tester.pumpAndSettle();

      // Verify selection
      expect(find.text('O+'), findsWidgets);
    });

    testWidgets('displays submit button', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: WalkInRegistrationScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Check for submit button
      expect(find.text('Register Walk-in Patient'), findsOneWidget);
      expect(find.byType(ElevatedButton), findsOneWidget);
    });

    testWidgets('shows error message when doctor selection is missing', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: WalkInRegistrationScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Fill in required name field
      final nameField = find.widgetWithText(TextFormField, 'Full Name *');
      await tester.enterText(nameField, 'John Doe');

      // Try to submit without selecting doctor
      final submitButton = find.text('Register Walk-in Patient');
      await tester.tap(submitButton);
      await tester.pumpAndSettle();

      // Should show snackbar message
      expect(find.text('Please select a doctor'), findsOneWidget);
    });

    testWidgets('displays section headers', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: WalkInRegistrationScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Check for section headers
      expect(find.text('Patient Information'), findsOneWidget);
      expect(find.text('Doctor Selection'), findsOneWidget);
    });

    testWidgets('has proper form field icons', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: WalkInRegistrationScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Check for icons
      expect(find.byIcon(Icons.person), findsOneWidget);
      expect(find.byIcon(Icons.email), findsOneWidget);
      expect(find.byIcon(Icons.phone), findsOneWidget);
      expect(find.byIcon(Icons.calendar_today), findsOneWidget);
      expect(find.byIcon(Icons.wc), findsOneWidget);
      expect(find.byIcon(Icons.bloodtype), findsOneWidget);
      expect(find.byIcon(Icons.home), findsOneWidget);
    });
  });
}
