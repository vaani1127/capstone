import 'api_client.dart';

/// Service for admin operations and statistics
class AdminService {
  final ApiClient _apiClient = ApiClient();

  /// Get system statistics for admin dashboard
  Future<Map<String, dynamic>> getSystemStatistics() async {
    try {
      // Fetch data from multiple endpoints and aggregate
      final users = await _apiClient.get('/users');
      final appointments = await _apiClient.get('/appointments/');
      final auditLogs = await _apiClient.get('/audit/logs?page=1&page_size=10');

      // /users/ and /appointments/ both return JSON arrays directly (not wrapped).
      final totalUsers = (users as List).length;
      final allAppointments = appointments as List;
      
      // Count appointments today
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final tomorrow = today.add(const Duration(days: 1));
      
      final appointmentsToday = allAppointments.where((apt) {
        final scheduledTime = DateTime.parse(apt['scheduled_time'] as String);
        return scheduledTime.isAfter(today) && scheduledTime.isBefore(tomorrow);
      }).length;
      
      // Count active doctors (users with Doctor role)
      final activeDoctors = (users as List)
          .where((user) => user['role'] == 'Doctor')
          .length;
      
      // Count pending appointments (scheduled or checked_in status)
      final pendingAppointments = allAppointments
          .where((apt) => 
              apt['status'] == 'scheduled' || 
              apt['status'] == 'checked_in')
          .length;
      
      return {
        'total_users': totalUsers,
        'appointments_today': appointmentsToday,
        'active_doctors': activeDoctors,
        'pending_appointments': pendingAppointments,
      };
    } catch (e) {
      throw Exception('Failed to fetch system statistics: $e');
    }
  }

  /// Get recent activity (appointments and registrations)
  Future<Map<String, dynamic>> getRecentActivity() async {
    try {
      // Fetch recent appointments — backend returns a JSON array directly.
      final appointments = await _apiClient.get('/appointments/');
      final allAppointments = appointments as List;
      
      // Sort by creation time and take last 5
      allAppointments.sort((a, b) {
        final aTime = DateTime.parse(a['created_at'] as String);
        final bTime = DateTime.parse(b['created_at'] as String);
        return bTime.compareTo(aTime);
      });
      
      final recentAppointments = allAppointments.take(5).toList();
      
      // Fetch recent users (registrations)
      final users = await _apiClient.get('/users');
      final allUsers = users as List;
      
      // Sort by creation time and take last 5
      allUsers.sort((a, b) {
        final aTime = DateTime.parse(a['created_at'] as String);
        final bTime = DateTime.parse(b['created_at'] as String);
        return bTime.compareTo(aTime);
      });
      
      final recentRegistrations = allUsers.take(5).toList();
      
      return {
        'recent_appointments': recentAppointments,
        'recent_registrations': recentRegistrations,
      };
    } catch (e) {
      throw Exception('Failed to fetch recent activity: $e');
    }
  }

  /// Get all users (for user management)
  Future<List<Map<String, dynamic>>> getAllUsers() async {
    try {
      final response = await _apiClient.get('/users');
      return List<Map<String, dynamic>>.from(response as List);
    } catch (e) {
      throw Exception('Failed to fetch users: $e');
    }
  }

  /// Create a new user (Admin only)
  Future<Map<String, dynamic>> createUser({
    required String name,
    required String email,
    required String password,
    required String role,
  }) async {
    try {
      final response = await _apiClient.post('/auth/register', {
        'name': name,
        'email': email,
        'password': password,
        'role': role,
      });
      return response as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to create user: $e');
    }
  }

  /// Update user details (Admin only)
  Future<Map<String, dynamic>> updateUser({
    required int userId,
    required String name,
    required String email,
    required String role,
  }) async {
    try {
      final response = await _apiClient.put('/users/$userId', {
        'name': name,
        'email': email,
        'role': role,
      });
      return response as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to update user: $e');
    }
  }

  /// Get audit logs with pagination and filters (Admin only)
  Future<Map<String, dynamic>> getAuditLogs({
    int page = 1,
    int pageSize = 20,
    DateTime? startDate,
    DateTime? endDate,
    int? userId,
    String? recordType,
  }) async {
    try {
      final queryParams = <String, String>{
        'page': page.toString(),
        'page_size': pageSize.toString(),
      };
      
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String();
      }
      
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String();
      }
      
      if (userId != null) {
        queryParams['user_id'] = userId.toString();
      }
      
      if (recordType != null) {
        queryParams['record_type'] = recordType;
      }
      
      final queryString = queryParams.entries
          .map((e) => '${e.key}=${Uri.encodeComponent(e.value)}')
          .join('&');
      
      final response = await _apiClient.get('/audit/logs?$queryString');
      return response as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to fetch audit logs: $e');
    }
  }

  /// Get tampering alerts (Admin only)
  Future<List<Map<String, dynamic>>> getTamperingAlerts() async {
    try {
      final response = await _apiClient.get('/audit/tampering-alerts');
      return List<Map<String, dynamic>>.from(response as List);
    } catch (e) {
      throw Exception('Failed to fetch tampering alerts: $e');
    }
  }

  /// Export audit logs in specified format (Admin only)
  Future<void> exportAuditLogs({
    required String format,
    DateTime? startDate,
    DateTime? endDate,
    int? userId,
    String? recordType,
  }) async {
    try {
      final queryParams = <String, String>{
        'format': format,
      };
      
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String();
      }
      
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String();
      }
      
      if (userId != null) {
        queryParams['user_id'] = userId.toString();
      }
      
      if (recordType != null) {
        queryParams['record_type'] = recordType;
      }
      
      final queryString = queryParams.entries
          .map((e) => '${e.key}=${Uri.encodeComponent(e.value)}')
          .join('&');
      
      // Note: In a real app, this would trigger a file download
      // For now, we just call the endpoint
      await _apiClient.get('/audit/export?$queryString');
    } catch (e) {
      throw Exception('Failed to export audit logs: $e');
    }
  }
}
