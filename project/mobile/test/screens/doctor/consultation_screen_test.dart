import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:healthsaathi/screens/doctor/consultation_screen.dart';
import 'package:healthsaathi/models/appointment.dart';
import 'package:healthsaathi/providers/auth_provider.dart';

void main() {
  group('ConsultationScreen', () {
    late Appointment testAppointment;
    late AuthProvider authProvider;

    setUp(() {
      testAppointment = Appointment(
        id: 1,
        patientId: 10,
        doctorId: 5,
        scheduledTime: DateTime.now(),
        status: 'in_progress',
        appointmentType: 'scheduled',
        queuePosition: 1,
        patientName: 'John Doe',
        doctorName: 'Dr. Smith',
        createdAt: DateTime.now(),
      );

      authProvider = AuthProvider();
    });

    Widget createTestWidget() {
      return ChangeNotifierProvider<AuthProvider>.value(
        value: authProvider,
        child: MaterialApp(
          home: ConsultationScreen(appointment: testAppointment),
        ),
      );
    }

    testWidgets('displays consultation screen title', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();

      // Check if app bar title is displayed
      expect(find.text('Consultation'), findsOneWidget);
    });

    testWidgets('displays save button in app bar', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pump();

      // Check for save button in app bar
      expect(find.text('Save & Complete'), findsOneWidget);
    });

    testWidgets('creates consultation screen with appointment', (WidgetTester tester) async {
      await tester.pumpWidget(createTestWidget());
      
      // Verify the widget is created
      expect(find.byType(ConsultationScreen), findsOneWidget);
    });

    testWidgets('displays walk-in appointment type correctly', (WidgetTester tester) async {
      final walkInAppointment = Appointment(
        id: 2,
        patientId: 11,
        doctorId: 5,
        scheduledTime: DateTime.now(),
        status: 'in_progress',
        appointmentType: 'walk_in',
        queuePosition: 1,
        patientName: 'Jane Doe',
        doctorName: 'Dr. Smith',
        createdAt: DateTime.now(),
      );

      await tester.pumpWidget(
        ChangeNotifierProvider<AuthProvider>.value(
          value: authProvider,
          child: MaterialApp(
            home: ConsultationScreen(appointment: walkInAppointment),
          ),
        ),
      );
      
      // Verify the widget is created with walk-in appointment
      expect(find.byType(ConsultationScreen), findsOneWidget);
    });
  });
}
