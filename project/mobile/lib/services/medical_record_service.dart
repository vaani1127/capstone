import '../models/medical_record.dart';
import 'api_client.dart';

/// Service for managing medical records
class MedicalRecordService {
  final ApiClient _apiClient = ApiClient();

  /// Get medical records for a patient (Doctor/Admin use — returns a plain list)
  Future<List<MedicalRecord>> getPatientRecords(int patientId) async {
    final response = await _apiClient.get('/medical-records/patient/$patientId');
    final records = (response as List)
        .map((json) => MedicalRecord.fromJson(json as Map<String, dynamic>))
        .toList();
    return records;
  }

  /// Get medical records for the current authenticated user
  Future<List<MedicalRecord>> getMyMedicalRecords() async {
    final response = await _apiClient.get('/medical-records/me');
    final records = (response as List)
        .map((json) => MedicalRecord.fromJson(json))
        .toList();
    return records;
  }

  /// Get a specific medical record
  Future<MedicalRecord> getRecord(int recordId) async {
    final response = await _apiClient.get('/medical-records/$recordId');
    return MedicalRecord.fromJson(response['record']);
  }

  /// Get version history of a medical record
  Future<List<MedicalRecord>> getRecordVersions(int recordId) async {
    final response = await _apiClient.get('/medical-records/$recordId/versions');
    final versions = (response['versions'] as List)
        .map((json) => MedicalRecord.fromJson(json))
        .toList();
    return versions;
  }

  /// Create a new consultation note (Doctor only)
  Future<MedicalRecord> createConsultationNote({
    required int patientId,
    required int appointmentId,
    required String consultationNotes,
    required String diagnosis,
  }) async {
    final response = await _apiClient.post('/medical-records', {
      'patient_id': patientId,
      'appointment_id': appointmentId,
      'consultation_notes': consultationNotes,
      'diagnosis': diagnosis,
    });
    return MedicalRecord.fromJson(response['record']);
  }

  /// Create a prescription (Doctor only)
  Future<MedicalRecord> createPrescription({
    required int patientId,
    required int appointmentId,
    required String prescription,
  }) async {
    final response = await _apiClient.post('/medical-records', {
      'patient_id': patientId,
      'appointment_id': appointmentId,
      'prescription': prescription,
    });
    return MedicalRecord.fromJson(response['record']);
  }

  /// Update a medical record (creates new version)
  Future<MedicalRecord> updateRecord({
    required int recordId,
    String? consultationNotes,
    String? diagnosis,
    String? prescription,
  }) async {
    final data = <String, dynamic>{};
    if (consultationNotes != null) data['consultation_notes'] = consultationNotes;
    if (diagnosis != null) data['diagnosis'] = diagnosis;
    if (prescription != null) data['prescription'] = prescription;

    final response = await _apiClient.put('/medical-records/$recordId', data);
    return MedicalRecord.fromJson(response['record']);
  }
}
