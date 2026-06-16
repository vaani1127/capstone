import '../models/procedure.dart';
import 'api_client.dart';

/// Service for recording and retrieving patient procedure records.
class ProcedureService {
  final ApiClient _apiClient = ApiClient();

  /// Return the authenticated patient's own procedure history (Patient only).
  Future<List<Procedure>> getMyProcedures() async {
    final response = await _apiClient.get('/procedures/me');
    final data = response as Map<String, dynamic>;
    return (data['procedures'] as List)
        .map((json) => Procedure.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  /// Return all procedures for [patientId] ordered by performed_at descending.
  Future<List<Procedure>> getPatientProcedures(int patientId) async {
    final response = await _apiClient.get('/procedures/patient/$patientId');
    final data = response as Map<String, dynamic>;
    return (data['procedures'] as List)
        .map((json) => Procedure.fromJson(json as Map<String, dynamic>))
        .toList();
  }
}
