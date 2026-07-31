import '../models/vitals.dart';
import 'api_client.dart';

/// Service for recording and retrieving patient vital signs.
class VitalsService {
  final ApiClient _apiClient = ApiClient();

  /// Record a new set of vitals for a patient (Nurse or Doctor only).
  ///
  /// All measurement fields are optional — submit only the ones collected.
  /// The server computes BMI when both [weightKg] and [heightCm] are provided.
  Future<Vitals> recordVitals({
    required int patientId,
    int? appointmentId,
    int? systolicBp,
    int? diastolicBp,
    int? heartRate,
    double? temperature,
    int? respiratoryRate,
    double? oxygenSaturation,
    double? weightKg,
    double? heightCm,
    String? notes,
  }) async {
    final body = <String, dynamic>{'patient_id': patientId};
    if (appointmentId != null) body['appointment_id'] = appointmentId;
    if (systolicBp != null) body['systolic_bp'] = systolicBp;
    if (diastolicBp != null) body['diastolic_bp'] = diastolicBp;
    if (heartRate != null) body['heart_rate'] = heartRate;
    if (temperature != null) body['temperature'] = temperature;
    if (respiratoryRate != null) body['respiratory_rate'] = respiratoryRate;
    if (oxygenSaturation != null) body['oxygen_saturation'] = oxygenSaturation;
    if (weightKg != null) body['weight_kg'] = weightKg;
    if (heightCm != null) body['height_cm'] = heightCm;
    if (notes != null && notes.isNotEmpty) body['notes'] = notes;

    final response = await _apiClient.post('/vitals/', body);
    return Vitals.fromJson(response as Map<String, dynamic>);
  }

  /// Return all vitals for [patientId] ordered by recorded_at descending.
  ///
  /// Accessible by Doctor, Nurse, Admin, or the patient themselves.
  Future<List<Vitals>> getPatientVitals(int patientId) async {
    return _apiClient.getList('/vitals/patient/$patientId', Vitals.fromJson, listKey: 'vitals');
  }

  /// Return the current patient's own vitals (Patient role only).
  ///
  /// Calls GET /vitals/me so the patient app does not need to know its own
  /// patient-table ID (which differs from the user ID).
  Future<List<Vitals>> getMyVitals() async {
    return _apiClient.getList('/vitals/me', Vitals.fromJson, listKey: 'vitals');
  }

  /// Return the single most recent vitals row for [patientId].
  ///
  /// Returns null when no vitals have been recorded yet (404 from server).
  Future<Vitals?> getLatestVitals(int patientId) async {
    try {
      final response =
          await _apiClient.get('/vitals/patient/$patientId/latest');
      return Vitals.fromJson(response as Map<String, dynamic>);
    } on ApiException catch (e) {
      if (e.statusCode == 404) return null;
      rethrow;
    }
  }
}
