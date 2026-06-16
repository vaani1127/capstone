import '../models/organization.dart';
import 'api_client.dart';

/// Result wrapper for paginated organisation responses.
class OrganizationPage {
  final List<Organization> items;
  final int total;
  final int page;
  final int pageSize;

  OrganizationPage({
    required this.items,
    required this.total,
    required this.page,
    required this.pageSize,
  });

  bool get hasMore => page * pageSize < total;
}

/// Service for retrieving healthcare organisation records.
class OrganizationService {
  final ApiClient _apiClient = ApiClient();

  /// Return a paginated page of organisations ordered by name.
  Future<OrganizationPage> getOrganizations({
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _apiClient.get(
      '/organizations/?page=$page&page_size=$pageSize',
    );
    final data = response as Map<String, dynamic>;
    return OrganizationPage(
      items: (data['organizations'] as List)
          .map((json) => Organization.fromJson(json as Map<String, dynamic>))
          .toList(),
      total: data['total'] as int,
      page: data['page'] as int,
      pageSize: data['page_size'] as int,
    );
  }

  /// Return a single organisation by ID.
  Future<Organization> getOrganization(int orgId) async {
    final response = await _apiClient.get('/organizations/$orgId');
    return Organization.fromJson(response as Map<String, dynamic>);
  }
}
