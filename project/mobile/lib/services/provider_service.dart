import '../models/provider.dart';
import 'api_client.dart';

/// Result wrapper for paginated provider responses.
class ProviderPage {
  final List<Provider> items;
  final int total;
  final int page;
  final int pageSize;

  ProviderPage({
    required this.items,
    required this.total,
    required this.page,
    required this.pageSize,
  });

  bool get hasMore => page * pageSize < total;
}

/// Service for retrieving healthcare provider records.
class ProviderService {
  final ApiClient _apiClient = ApiClient();

  /// Return the distinct speciality values for the filter dropdown.
  Future<List<String>> getSpecialities() async {
    final response = await _apiClient.get('/providers/by-speciality');
    return (response as List).map((e) => e as String).toList();
  }

  /// Return a paginated page of providers, optionally filtered by [speciality].
  Future<ProviderPage> getProviders({
    String? speciality,
    int page = 1,
    int pageSize = 20,
  }) async {
    final qs = StringBuffer('?page=$page&page_size=$pageSize');
    if (speciality != null && speciality.isNotEmpty) {
      qs.write('&speciality=${Uri.encodeComponent(speciality)}');
    }
    final response = await _apiClient.get('/providers/$qs');
    final data = response as Map<String, dynamic>;
    return ProviderPage(
      items: (data['providers'] as List)
          .map((json) => Provider.fromJson(json as Map<String, dynamic>))
          .toList(),
      total: data['total'] as int,
      page: data['page'] as int,
      pageSize: data['page_size'] as int,
    );
  }

  /// Return a single provider by ID.
  Future<Provider> getProvider(int providerId) async {
    final response = await _apiClient.get('/providers/$providerId');
    return Provider.fromJson(response as Map<String, dynamic>);
  }
}
