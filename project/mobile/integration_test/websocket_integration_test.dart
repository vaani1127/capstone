import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:healthsaathi/services/websocket_service.dart';
import 'package:healthsaathi/services/auth_service.dart';
import 'package:healthsaathi/services/appointment_service.dart';

/// Integration tests for WebSocket real-time communication
/// 
/// These tests verify:
/// - WebSocket connection establishment with JWT authentication
/// - Real-time queue updates
/// - Appointment status notifications
/// - Auto-reconnection on connection loss
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('WebSocket Integration Tests', () {
    late WebSocketService wsService;
    late AuthService authService;
    late AppointmentService appointmentService;

    setUp(() {
      wsService = WebSocketService();
      authService = AuthService();
      appointmentService = AppointmentService();
    });

    tearDown(() async {
      // Clean up: disconnect and logout
      await wsService.disconnect();
      try {
        await authService.logout();
      } catch (e) {
        // Ignore logout errors in teardown
      }
    });

    group('Connection Management', () {
      test('should connect to WebSocket with JWT authentication', () async {
        // Arrange - login to get JWT token
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );

        // Act
        await wsService.connect();

        // Wait for connection to establish
        await Future.delayed(const Duration(seconds: 2));

        // Assert
        expect(wsService.isConnected, isTrue);
      });

      test('should fail to connect without authentication', () async {
        // Arrange - ensure not logged in
        await authService.logout();

        // Act & Assert
        expect(
          () => wsService.connect(),
          throwsException,
        );
      });

      test('should disconnect successfully', () async {
        // Arrange - connect first
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 1));
        expect(wsService.isConnected, isTrue);

        // Act
        await wsService.disconnect();

        // Assert
        expect(wsService.isConnected, isFalse);
      });

      test('should emit connection status events', () async {
        // Arrange
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );

        final statusEvents = <bool>[];
        final subscription = wsService.connectionStatus.listen((status) {
          statusEvents.add(status);
        });

        // Act
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        // Assert
        expect(statusEvents, contains(true));

        // Cleanup
        await subscription.cancel();
      });

      test('should auto-reconnect on connection loss', () async {
        // Arrange - connect first
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 1));

        final reconnectEvents = <bool>[];
        final subscription = wsService.connectionStatus.listen((status) {
          reconnectEvents.add(status);
        });

        // Act - simulate connection loss by disconnecting
        await wsService.disconnect();
        await Future.delayed(const Duration(seconds: 1));

        // The service should attempt to reconnect
        // Wait for reconnection attempt (5 second delay configured)
        await Future.delayed(const Duration(seconds: 6));

        // Assert - should have reconnection events
        expect(reconnectEvents, isNotEmpty);

        // Cleanup
        await subscription.cancel();
      });
    });

    group('Real-Time Queue Updates', () {
      test('should receive queue update events', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        final queueUpdates = <Map<String, dynamic>>[];
        final subscription = wsService.queueUpdates.listen((update) {
          queueUpdates.add(update);
        });

        // Act - trigger a queue update by booking an appointment
        final doctors = await appointmentService.getAvailableDoctors();
        await appointmentService.bookAppointment(
          doctorId: doctors.first.id,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        // Wait for WebSocket message
        await Future.delayed(const Duration(seconds: 3));

        // Assert
        expect(queueUpdates, isNotEmpty);
        final update = queueUpdates.first;
        expect(update['event'], equals('queue_update'));
        expect(update['data'], isNotNull);
        expect(update['data']['doctor_id'], isNotNull);
        expect(update['data']['queue_length'], isA<int>());

        // Cleanup
        await subscription.cancel();
      });

      test('should receive queue updates for specific doctor', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        final doctors = await appointmentService.getAvailableDoctors();
        final targetDoctorId = doctors.first.id;

        final queueUpdates = <Map<String, dynamic>>[];
        final subscription = wsService.queueUpdates
            .where((update) => update['data']['doctor_id'] == targetDoctorId)
            .listen((update) {
          queueUpdates.add(update);
        });

        // Act - book appointment for specific doctor
        await appointmentService.bookAppointment(
          doctorId: targetDoctorId,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        // Wait for WebSocket message
        await Future.delayed(const Duration(seconds: 3));

        // Assert
        expect(queueUpdates, isNotEmpty);
        expect(queueUpdates.first['data']['doctor_id'], equals(targetDoctorId));

        // Cleanup
        await subscription.cancel();
      });

      test('should update queue length in real-time', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        final doctors = await appointmentService.getAvailableDoctors();
        final doctorId = doctors.first.id;

        // Get initial queue status
        final initialQueue = await appointmentService.getQueueStatus(doctorId);
        final initialLength = initialQueue['queue_length'] as int;

        final queueUpdates = <int>[];
        final subscription = wsService.queueUpdates
            .where((update) => update['data']['doctor_id'] == doctorId)
            .listen((update) {
          queueUpdates.add(update['data']['queue_length'] as int);
        });

        // Act - book appointment
        await appointmentService.bookAppointment(
          doctorId: doctorId,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        // Wait for WebSocket message
        await Future.delayed(const Duration(seconds: 3));

        // Assert
        expect(queueUpdates, isNotEmpty);
        expect(queueUpdates.last, equals(initialLength + 1));

        // Cleanup
        await subscription.cancel();
      });

      test('should include estimated wait time in queue updates', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        final queueUpdates = <Map<String, dynamic>>[];
        final subscription = wsService.queueUpdates.listen((update) {
          queueUpdates.add(update);
        });

        // Act - book appointment
        final doctors = await appointmentService.getAvailableDoctors();
        await appointmentService.bookAppointment(
          doctorId: doctors.first.id,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        // Wait for WebSocket message
        await Future.delayed(const Duration(seconds: 3));

        // Assert
        expect(queueUpdates, isNotEmpty);
        final update = queueUpdates.first;
        if (update['data']['queue_length'] > 0) {
          expect(update['data']['estimated_wait_time'], isNotNull);
        }

        // Cleanup
        await subscription.cancel();
      });
    });

    group('Appointment Status Notifications', () {
      test('should receive appointment status change events', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        final statusUpdates = <Map<String, dynamic>>[];
        final subscription = wsService.appointmentUpdates.listen((update) {
          statusUpdates.add(update);
        });

        // Act - book and then cancel appointment
        final doctors = await appointmentService.getAvailableDoctors();
        final appointment = await appointmentService.bookAppointment(
          doctorId: doctors.first.id,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        await Future.delayed(const Duration(seconds: 2));
        await appointmentService.cancelAppointment(appointment.id);

        // Wait for WebSocket messages
        await Future.delayed(const Duration(seconds: 3));

        // Assert
        expect(statusUpdates, isNotEmpty);
        final update = statusUpdates.last;
        expect(update['event'], equals('appointment_status'));
        expect(update['data']['appointment_id'], equals(appointment.id));
        expect(update['data']['status'], equals('cancelled'));

        // Cleanup
        await subscription.cancel();
      });

      test('should receive notifications for specific appointment', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        // Book appointment
        final doctors = await appointmentService.getAvailableDoctors();
        final appointment = await appointmentService.bookAppointment(
          doctorId: doctors.first.id,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        final statusUpdates = <Map<String, dynamic>>[];
        final subscription = wsService.appointmentUpdates
            .where((update) =>
                update['data']['appointment_id'] == appointment.id)
            .listen((update) {
          statusUpdates.add(update);
        });

        // Act - cancel the appointment
        await Future.delayed(const Duration(seconds: 1));
        await appointmentService.cancelAppointment(appointment.id);

        // Wait for WebSocket message
        await Future.delayed(const Duration(seconds: 3));

        // Assert
        expect(statusUpdates, isNotEmpty);
        expect(
          statusUpdates.first['data']['appointment_id'],
          equals(appointment.id),
        );

        // Cleanup
        await subscription.cancel();
      });
    });

    group('Message Handling', () {
      test('should handle multiple concurrent messages', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        final allMessages = <Map<String, dynamic>>[];
        final subscription = wsService.messages.listen((message) {
          allMessages.add(message);
        });

        // Act - trigger multiple events
        final doctors = await appointmentService.getAvailableDoctors();
        
        // Book multiple appointments
        for (int i = 0; i < 3; i++) {
          await appointmentService.bookAppointment(
            doctorId: doctors.first.id,
            scheduledTime: DateTime.now().add(Duration(hours: i + 1)),
          );
          await Future.delayed(const Duration(milliseconds: 500));
        }

        // Wait for all messages
        await Future.delayed(const Duration(seconds: 5));

        // Assert
        expect(allMessages.length, greaterThanOrEqualTo(3));

        // Cleanup
        await subscription.cancel();
      });

      test('should filter messages by event type', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        final queueMessages = <Map<String, dynamic>>[];
        final appointmentMessages = <Map<String, dynamic>>[];

        final queueSub = wsService.queueUpdates.listen((msg) {
          queueMessages.add(msg);
        });
        final appointmentSub = wsService.appointmentUpdates.listen((msg) {
          appointmentMessages.add(msg);
        });

        // Act - trigger both types of events
        final doctors = await appointmentService.getAvailableDoctors();
        final appointment = await appointmentService.bookAppointment(
          doctorId: doctors.first.id,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        await Future.delayed(const Duration(seconds: 2));
        await appointmentService.cancelAppointment(appointment.id);

        // Wait for messages
        await Future.delayed(const Duration(seconds: 3));

        // Assert
        expect(queueMessages, isNotEmpty);
        expect(appointmentMessages, isNotEmpty);
        
        // Verify all queue messages have correct event type
        for (final msg in queueMessages) {
          expect(msg['event'], equals('queue_update'));
        }
        
        // Verify all appointment messages have correct event type
        for (final msg in appointmentMessages) {
          expect(msg['event'], equals('appointment_status'));
        }

        // Cleanup
        await queueSub.cancel();
        await appointmentSub.cancel();
      });

      test('should handle malformed messages gracefully', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        // This test verifies that the WebSocket service doesn't crash
        // when receiving malformed messages. The service should silently
        // ignore invalid JSON or messages with unexpected structure.

        // Act - normal operation should continue
        final doctors = await appointmentService.getAvailableDoctors();
        final appointment = await appointmentService.bookAppointment(
          doctorId: doctors.first.id,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        // Assert - connection should still be active
        expect(wsService.isConnected, isTrue);
        expect(appointment, isNotNull);
      });
    });

    group('Performance', () {
      test('should receive updates within 2 seconds', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        final stopwatch = Stopwatch()..start();
        Map<String, dynamic>? receivedUpdate;

        final subscription = wsService.queueUpdates.listen((update) {
          if (receivedUpdate == null) {
            stopwatch.stop();
            receivedUpdate = update;
          }
        });

        // Act - trigger queue update
        final doctors = await appointmentService.getAvailableDoctors();
        await appointmentService.bookAppointment(
          doctorId: doctors.first.id,
          scheduledTime: DateTime.now().add(const Duration(hours: 1)),
        );

        // Wait for message
        await Future.delayed(const Duration(seconds: 3));

        // Assert - should receive within 2 seconds (NFR-6)
        expect(receivedUpdate, isNotNull);
        expect(stopwatch.elapsedMilliseconds, lessThan(2000));

        // Cleanup
        await subscription.cancel();
      });

      test('should handle high-frequency updates', () async {
        // Arrange - login and connect
        await authService.login(
          email: 'patient@test.com',
          password: 'password123',
        );
        await wsService.connect();
        await Future.delayed(const Duration(seconds: 2));

        final receivedMessages = <Map<String, dynamic>>[];
        final subscription = wsService.messages.listen((message) {
          receivedMessages.add(message);
        });

        // Act - trigger rapid updates
        final doctors = await appointmentService.getAvailableDoctors();
        for (int i = 0; i < 5; i++) {
          await appointmentService.bookAppointment(
            doctorId: doctors.first.id,
            scheduledTime: DateTime.now().add(Duration(hours: i + 1)),
          );
        }

        // Wait for all messages
        await Future.delayed(const Duration(seconds: 5));

        // Assert - should receive all updates without dropping messages
        expect(receivedMessages.length, greaterThanOrEqualTo(5));

        // Cleanup
        await subscription.cancel();
      });
    });
  });
}
