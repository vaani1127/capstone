import '../models/appointment.dart';
import '../models/doctor.dart';
import 'api_client.dart';

/// Service for managing appointments.
///
/// All backend list endpoints return a JSON array directly (not wrapped).
/// All backend single-object endpoints return the object directly (not wrapped).
class AppointmentService {
  final ApiClient _apiClient = ApiClient();

  /// Get all appointments for the current user (role-based filtering applied server-side).
  Future<List<Appointment>> getAppointments() async {
    final response = await _apiClient.get('/appointments/');
    return (response as List)
        .map((json) => Appointment.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  /// Get appointments filtered by patient ID (Admin/Nurse only).
  Future<List<Appointment>> getPatientAppointments(int patientId) async {
    final response = await _apiClient.get('/appointments/?patient_id=$patientId');
    return (response as List)
        .map((json) => Appointment.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  /// Get appointments filtered by doctor ID (Admin/Nurse only).
  Future<List<Appointment>> getDoctorAppointments(int doctorId) async {
    final response = await _apiClient.get('/appointments/?doctor_id=$doctorId');
    return (response as List)
        .map((json) => Appointment.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  /// Book a new appointment (Patient only).
  Future<Appointment> bookAppointment({
    required int doctorId,
    required DateTime scheduledTime,
  }) async {
    final response = await _apiClient.post('/appointments/', {
      'doctor_id': doctorId,
      'scheduled_time': scheduledTime.toUtc().toIso8601String(),
    });
    // Backend returns AppointmentWithDetails directly (not wrapped).
    return Appointment.fromJson(response as Map<String, dynamic>);
  }

  /// Cancel an appointment.
  Future<void> cancelAppointment(int appointmentId) async {
    await _apiClient.delete('/appointments/$appointmentId');
  }

  /// Reschedule an appointment to a new time.
  ///
  /// Uses the general PUT /{id} endpoint with only [scheduledTime] set.
  Future<Appointment> rescheduleAppointment({
    required int appointmentId,
    required DateTime newScheduledTime,
  }) async {
    final response = await _apiClient.put('/appointments/$appointmentId', {
      'scheduled_time': newScheduledTime.toUtc().toIso8601String(),
    });
    // Backend returns AppointmentWithDetails directly (not wrapped).
    return Appointment.fromJson(response as Map<String, dynamic>);
  }

  /// List available doctors (any authenticated user).
  Future<List<Doctor>> getAvailableDoctors() async {
    final response = await _apiClient.get('/users/doctors');
    // Backend returns a JSON array of DoctorProfileResponse.
    return (response as List)
        .map((json) => Doctor.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  /// Get queue status for a specific doctor.
  Future<Map<String, dynamic>> getQueueStatus(int doctorId) async {
    final response = await _apiClient.get('/queue/doctor/$doctorId');
    return response as Map<String, dynamic>;
  }

  /// Register a walk-in patient (Nurse/Admin only).
  ///
  /// The backend finds or creates the patient from [patientEmail]/[patientPhone].
  /// [patientName] is required by the server.
  Future<Appointment> registerWalkIn({
    required int doctorId,
    required String patientName,
    String? patientEmail,
    String? patientPhone,
    DateTime? dateOfBirth,
    String? gender,
    String? address,
    String? bloodGroup,
  }) async {
    final Map<String, dynamic> requestData = {
      'doctor_id': doctorId,
      'patient_name': patientName,
    };

    if (patientEmail != null && patientEmail.isNotEmpty) {
      requestData['patient_email'] = patientEmail;
    }
    if (patientPhone != null && patientPhone.isNotEmpty) {
      requestData['patient_phone'] = patientPhone;
    }
    if (dateOfBirth != null) {
      requestData['date_of_birth'] = dateOfBirth.toUtc().toIso8601String();
    }
    if (gender != null && gender.isNotEmpty) {
      requestData['gender'] = gender;
    }
    if (address != null && address.isNotEmpty) {
      requestData['address'] = address;
    }
    if (bloodGroup != null && bloodGroup.isNotEmpty) {
      requestData['blood_group'] = bloodGroup;
    }

    final response = await _apiClient.post('/appointments/walk-in', requestData);
    // Backend returns AppointmentWithDetails directly (not wrapped).
    return Appointment.fromJson(response as Map<String, dynamic>);
  }
}
