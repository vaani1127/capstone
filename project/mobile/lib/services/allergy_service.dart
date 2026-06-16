import '../models/allergy.dart';
import 'api_client.dart';

/// Service for recording and retrieving patient allergy records.
class AllergyService {
  final ApiClient _apiClient = ApiClient();

  /// Record a new allergy for a patient (Doctor or Nurse only).
  Future<Allergy> recordAllergy({
    required int patientId,
    required String allergen,
    String? reaction,
    required String severity,
    DateTime? onsetDate,
    String? notes,
  }) async {
    final body = <String, dynamic>{
      'patient_id': patientId,
      'allergen': allergen,
      'severity': severity,
    };
    if (reaction != null && reaction.isNotEmpty) body['reaction'] = reaction;
    if (onsetDate != null) {
      body['onset_date'] =
          '${onsetDate.year.toString().padLeft(4, '0')}-'
          '${onsetDate.month.toString().padLeft(2, '0')}-'
          '${onsetDate.day.toString().padLeft(2, '0')}';
    }
    if (notes != null && notes.isNotEmpty) body['notes'] = notes;

    final response = await _apiClient.post('/allergies/', body);
    return Allergy.fromJson(response as Map<String, dynamic>);
  }

  /// Return allergy records for [patientId] (Doctor, Nurse, Admin, or patient themselves).
  ///
  /// By default only active allergies are returned.
  /// Set [includeInactive] to true to include deactivated records.
  Future<List<Allergy>> getPatientAllergies(
    int patientId, {
    bool includeInactive = false,
  }) async {
    final qs = includeInactive ? '?include_inactive=true' : '';
    final response = await _apiClient.get('/allergies/patient/$patientId$qs');
    final data = response as Map<String, dynamic>;
    return (data['allergies'] as List)
        .map((json) => Allergy.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  /// Return the authenticated patient's own active allergies (Patient only).
  ///
  /// Calls GET /allergies/me so the patient app does not need to know its
  /// patient-table ID.
  Future<List<Allergy>> getMyAllergies() async {
    final response = await _apiClient.get('/allergies/me');
    final data = response as Map<String, dynamic>;
    return (data['allergies'] as List)
        .map((json) => Allergy.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  /// Deactivate an allergy record (Doctor only).
  ///
  /// Returns the updated [Allergy] with is_active=false.
  Future<Allergy> deactivateAllergy(int allergyId) async {
    final response = await _apiClient.patch('/allergies/$allergyId/deactivate', {});
    return Allergy.fromJson(response as Map<String, dynamic>);
  }
}
