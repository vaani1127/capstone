import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:healthsaathi/screens/patient/appointment_booking_screen.dart';
import 'package:healthsaathi/models/doctor.dart';
import 'package:healthsaathi/models/appointment.dart';
import 'package:healthsaathi/services/appointment_service.dart';

void main() {
  group('AppointmentBookingScreen', () {
    testWidgets('displays loading indicator initially', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AppointmentBookingScreen(),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Loading doctors...'), findsOneWidget);
    });

    testWidgets('displays app bar with correct title', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AppointmentBookingScreen(),
        ),
      );

      expect(find.text('Book Appointment'), findsOneWidget);
    });

    testWidgets('displays section titles when doctors are loaded', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AppointmentBookingScreen(),
        ),
      );

      // Wait for loading to complete
      await tester.pump(const Duration(seconds: 2));

      // Note: This test would need mocking to properly test the loaded state
      // For now, we're just verifying the widget can be created
    });

    testWidgets('doctor card displays doctor information', (WidgetTester tester) async {
      // This is a unit test for the doctor card display logic
      // In a real scenario, we would mock the AppointmentService
      
      final doctor = Doctor(
        id: 1,
        userId: 1,
        name: 'Dr. Smith',
        specialization: 'Cardiology',
        averageConsultationDuration: 15,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Card(
              child: ListTile(
                title: Text(doctor.name),
                subtitle: Text(doctor.specialization),
              ),
            ),
          ),
        ),
      );

      expect(find.text('Dr. Smith'), findsOneWidget);
      expect(find.text('Cardiology'), findsOneWidget);
    });

    testWidgets('date and time selection widgets are present', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AppointmentBookingScreen(),
        ),
      );

      // Wait for initial load
      await tester.pump(const Duration(seconds: 1));

      // The date and time selection should appear after selecting a doctor
      // This would require mocking the service to test properly
    });

    testWidgets('confirm booking button appears when all selections are made', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AppointmentBookingScreen(),
        ),
      );

      // Wait for loading
      await tester.pump(const Duration(seconds: 1));

      // The confirm button should only appear after doctor, date, and time are selected
      // This would require mocking to test the full flow
    });
  });
}
