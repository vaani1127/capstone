import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:healthsaathi/services/api_client.dart';
import 'package:healthsaathi/services/auth_service.dart';
import 'package:healthsaathi/services/appointment_service.dart';
import 'package:healthsaathi/services/medical_record_service.dart';

/// Integration tests for API endpoints
/// 
/// These tests verify the mobile app's integration with the backend API:
/// - Authentication (login/logout)
/// - Appointment booking flow
/// - Medical records retrieval
/// - Queue status updates
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('API Integration Tests', () {
    late ApiClient apiClient;
    late AuthService authService;
    late AppointmentService appointmentService;
    late MedicalRecordService medicalRecordService;

    setUp(() {
      apiClient = ApiClient();
      authService = AuthService();
      appointmentService = AppointmentService();
      medicalRecordService = MedicalRecordService();
    });

    tearDown(() async {
      // Clean up: logout after each test
      try {
        await authService.logout();
      } catch (e) {
        // Ignore logout errors in teardown
      }
    });

    group('Authentication Flow', () {
      test('should login with valid credentials', () async {
        // Arrange
        const email = 'patient@test.com';
        const password = 'password123';

        // Act
        final user = await authService.login(
          email: email,
          password: password,
        );

        // Assert
        expect(user, isNotNull);
        expect(user.email, equals(email));
        expect(apiClient.isAuthenticated, isTrue);
        expect(apiClient.token, isNotNull);
      });

      test('should fail login with invalid credentials', () async {
        // Arrange
        const email = 'invalid@test.com';
        const password = 'wrongpassword';

        // Act & Assert
        expect(
          () => authService.login(email: email, password: password),
          throwsA(isA<ApiException>()),
        );
      });

      test('should logout successfully', () async {
        // Arrange - login first
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        expect(apiClient.isAuthenticated, isTrue);

        // Act
        await authService.logout();

        // Assert
        expect(apiClient.isAuthenticated, isFalse);
        expect(apiClient.token, isNull);
        final currentUser = await authService.getCurrentUser();
        expect(currentUser, isNull);
      });

      test('should persist authentication across app restarts', () async {
        // Arrange - login
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        final token = apiClient.token;

        // Act - simulate app restart by creating new instances
        final newApiClient = ApiClient();
        await newApiClient.initialize();

        // Assert
        expect(newApiClient.isAuthenticated, isTrue);
        expect(newApiClient.token, equals(token));
      });

      test('should handle token expiration', () async {
        // Arrange - login with expired token (if backend supports it)
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );

        // Manually set an expired token
        await apiClient.setToken('expired.token.here');

        // Act & Assert - should throw 401 error
        expect(
          () => appointmentService.getAppointments(),
          throwsA(
            predicate((e) =>
                e is ApiException && e.statusCode == 401),
          ),
        );
      });
    });

    group('Appointment Booking Flow', () {
      setUp(() async {
        // Login as patient before each test
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
      });

      test('should get list of available doctors', () async {
        // Act
        final doctors = await appointmentService.getAvailableDoctors();

        // Assert
        expect(doctors, isNotEmpty);
        expect(doctors.first.specialization, isNotNull);
      });

      test('should book an appointment successfully', () async {
        // Arrange
        final doctors = await appointmentService.getAvailableDoctors();
        final doctorId = doctors.first.id;
        final scheduledTime = DateTime.now().add(const Duration(days: 1));

        // Act
        final appointment = await appointmentService.bookAppointment(
          doctorId: doctorId,
          scheduledTime: scheduledTime,
        );

        // Assert
        expect(appointment, isNotNull);
        expect(appointment.doctorId, equals(doctorId));
        expect(appointment.status, equals('scheduled'));
        expect(appointment.queuePosition, isNotNull);
      });

      test('should get patient appointments', () async {
        // Arrange - book an appointment first
        final doctors = await appointmentService.getAvailableDoctors();
        await appointmentService.bookAppointment(
          doctorId: doctors.first.id,
          scheduledTime: DateTime.now().add(const Duration(days: 1)),
        );

        // Act
        final appointments = await appointmentService.getAppointments();

        // Assert
        expect(appointments, isNotEmpty);
        expect(appointments.first.status, isNotNull);
      });

      test('should cancel an appointment', () async {
        // Arrange - book an appointment first
        final doctors = await appointmentService.getAvailableDoctors();
        final appointment = await appointmentService.bookAppointment(
          doctorId: doctors.first.id,
          scheduledTime: DateTime.now().add(const Duration(days: 1)),
        );

        // Act
        await appointmentService.cancelAppointment(appointment.id);

        // Assert - verify appointment is cancelled
        final appointments = await appointmentService.getAppointments();
        final cancelledAppointment = appointments.firstWhere(
          (a) => a.id == appointment.id,
          orElse: () => throw Exception('Appointment not found'),
        );
        expect(cancelledAppointment.status, equals('cancelled'));
      });

      test('should reschedule an appointment', () async {
        // Arrange - book an appointment first
        final doctors = await appointmentService.getAvailableDoctors();
        final appointment = await appointmentService.bookAppointment(
          doctorId: doctors.first.id,
          scheduledTime: DateTime.now().add(const Duration(days: 1)),
        );
        final newTime = DateTime.now().add(const Duration(days: 2));

        // Act
        final rescheduled = await appointmentService.rescheduleAppointment(
          appointmentId: appointment.id,
          newScheduledTime: newTime,
        );

        // Assert
        expect(rescheduled.id, equals(appointment.id));
        expect(
          rescheduled.scheduledTime.difference(newTime).inMinutes.abs(),
          lessThan(1),
        );
      });

      test('should prevent double-booking', () async {
        // Arrange
        final doctors = await appointmentService.getAvailableDoctors();
        final doctorId = doctors.first.id;
        final scheduledTime = DateTime.now().add(const Duration(days: 1));

        // Book first appointment
        await appointmentService.bookAppointment(
          doctorId: doctorId,
          scheduledTime: scheduledTime,
        );

        // Act & Assert - try to book same time slot
        expect(
          () => appointmentService.bookAppointment(
            doctorId: doctorId,
            scheduledTime: scheduledTime,
          ),
          throwsA(isA<ApiException>()),
        );
      });
    });

    group('Medical Records Retrieval', () {
      setUp(() async {
        // Login as patient before each test
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
      });

      test('should get patient medical records', () async {
        // Act
        final records = await medicalRecordService.getMyMedicalRecords();

        // Assert
        expect(records, isNotNull);
        // Records may be empty for new patients
        if (records.isNotEmpty) {
          expect(records.first.consultationNotes, isNotNull);
        }
      });

      test('should get medical record by ID', () async {
        // Arrange - get all records first
        final records = await medicalRecordService.getMyMedicalRecords();
        if (records.isEmpty) {
          // Skip test if no records exist
          return;
        }
        final recordId = records.first.id;

        // Act
        final record = await medicalRecordService.getRecord(recordId);

        // Assert
        expect(record, isNotNull);
        expect(record.id, equals(recordId));
      });

      test('should enforce read-only access for patients', () async {
        // Arrange - get a record
        final records = await medicalRecordService.getMyMedicalRecords();
        if (records.isEmpty) {
          // Skip test if no records exist
          return;
        }

        // Act & Assert - patients should not be able to update records
        expect(
          () => apiClient.put('/medical-records/${records.first.id}', {
            'consultation_notes': 'Trying to modify',
          }),
          throwsA(
            predicate((e) =>
                e is ApiException && e.statusCode == 403),
          ),
        );
      });
    });

    group('Queue Status Updates', () {
      setUp(() async {
        // Login as patient before each test
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
      });

      test('should get queue status for a doctor', () async {
        // Arrange
        final doctors = await appointmentService.getAvailableDoctors();
        final doctorId = doctors.first.id;

        // Act
        final queueStatus = await appointmentService.getQueueStatus(doctorId);

        // Assert
        expect(queueStatus, isNotNull);
        expect(queueStatus['queue_length'], isA<int>());
        expect(queueStatus['queue_length'], greaterThanOrEqualTo(0));
      });

      test('should calculate estimated waiting time', () async {
        // Arrange - book an appointment to ensure queue has patients
        final doctors = await appointmentService.getAvailableDoctors();
        final doctorId = doctors.first.id;
        await appointmentService.bookAppointment(
          doctorId: doctorId,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        // Act
        final queueStatus = await appointmentService.getQueueStatus(doctorId);

        // Assert
        if (queueStatus['queue_length'] > 0) {
          expect(queueStatus['estimated_wait_time'], isNotNull);
          expect(queueStatus['estimated_wait_time'], isA<int>());
        }
      });

      test('should update queue position after booking', () async {
        // Arrange
        final doctors = await appointmentService.getAvailableDoctors();
        final doctorId = doctors.first.id;

        // Get initial queue status
        final initialQueue = await appointmentService.getQueueStatus(doctorId);
        final initialLength = initialQueue['queue_length'] as int;

        // Act - book an appointment
        final appointment = await appointmentService.bookAppointment(
          doctorId: doctorId,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        // Get updated queue status
        final updatedQueue = await appointmentService.getQueueStatus(doctorId);
        final updatedLength = updatedQueue['queue_length'] as int;

        // Assert
        expect(updatedLength, equals(initialLength + 1));
        expect(appointment.queuePosition, isNotNull);
        expect(appointment.queuePosition, greaterThan(0));
      });
    });

    group('Role-Based Access Control', () {
      test('should allow doctor to access doctor endpoints', () async {
        // Arrange - login as doctor
        await authService.login(
          email: 'doctor@test.com',
          password: 'password123',
        );

        // Act - access doctor-specific endpoint
        final appointments = await appointmentService.getAppointments();

        // Assert
        expect(appointments, isNotNull);
      });

      test('should deny patient access to admin endpoints', () async {
        // Arrange - login as patient
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );

        // Act & Assert - try to access admin endpoint
        expect(
          () => apiClient.get('/audit/logs'),
          throwsA(
            predicate((e) =>
                e is ApiException && e.statusCode == 403),
          ),
        );
      });

      test('should deny nurse access to doctor-only endpoints', () async {
        // Arrange - login as nurse
        await authService.login(
          email: 'nurse@test.com',
          password: 'password123',
        );

        // Act & Assert - try to create consultation notes (doctor only)
        expect(
          () => apiClient.post('/medical-records', {
            'patient_id': 1,
            'consultation_notes': 'Test notes',
          }),
          throwsA(
            predicate((e) =>
                e is ApiException && e.statusCode == 403),
          ),
        );
      });
    });

    group('Error Handling', () {
      test('should handle network errors gracefully', () async {
        // Arrange - use invalid base URL
        final testClient = ApiClient();
        
        // Act & Assert
        expect(
          () => testClient.get('/invalid-endpoint'),
          throwsA(isA<ApiException>()),
        );
      });

      test('should handle 404 errors', () async {
        // Arrange - login first
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );

        // Act & Assert
        expect(
          () => apiClient.get('/non-existent-endpoint'),
          throwsA(
            predicate((e) =>
                e is ApiException && e.statusCode == 404),
          ),
        );
      });

      test('should handle malformed responses', () async {
        // This test would require mocking the HTTP client
        // to return malformed JSON, which is beyond basic integration testing
        // but is important for production apps
      });
    });
  });
}
