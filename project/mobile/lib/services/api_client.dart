import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';

/// API client with JWT token management
class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  ApiClient._internal();

  String? _token;
  String? _refreshToken;

  /// Initialize the API client by loading stored tokens
  Future<void> initialize() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(AppConfig.tokenKey);
    _refreshToken = prefs.getString(AppConfig.refreshTokenKey);
  }

  /// Get the current JWT token
  String? get token => _token;

  /// Check if user is authenticated
  bool get isAuthenticated => _token != null;

  /// Set the JWT token and store it
  Future<void> setToken(String token, {String? refreshToken}) async {
    _token = token;
    _refreshToken = refreshToken;
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConfig.tokenKey, token);
    if (refreshToken != null) {
      await prefs.setString(AppConfig.refreshTokenKey, refreshToken);
    }
  }

  /// Clear the JWT token
  Future<void> clearToken() async {
    _token = null;
    _refreshToken = null;
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConfig.tokenKey);
    await prefs.remove(AppConfig.refreshTokenKey);
    await prefs.remove(AppConfig.userKey);
  }

  /// Get headers with authentication
  Map<String, String> _getHeaders({bool includeAuth = true}) {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    if (includeAuth && _token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }

    return headers;
  }

  /// Handle API response
  dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) {
        return null;
      }
      return json.decode(response.body);
    } else if (response.statusCode == 401) {
      // Token expired or invalid
      throw ApiException('Unauthorized', statusCode: 401);
    } else if (response.statusCode == 403) {
      throw ApiException('Forbidden', statusCode: 403);
    } else if (response.statusCode == 404) {
      throw ApiException('Not found', statusCode: 404);
    } else {
      final body = json.decode(response.body);
      final message = body['error']?['message'] ?? body['detail'] ?? 'Request failed';
      throw ApiException(message, statusCode: response.statusCode);
    }
  }

  /// GET request
  Future<dynamic> get(String endpoint, {bool includeAuth = true}) async {
    try {
      final url = Uri.parse('${AppConfig.fullApiUrl}$endpoint');
      final response = await http
          .get(url, headers: _getHeaders(includeAuth: includeAuth))
          .timeout(AppConfig.apiTimeout);
      
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection');
    } on HttpException {
      throw ApiException('Server error');
    } on FormatException {
      throw ApiException('Invalid response format');
    }
  }

  /// POST request
  Future<dynamic> post(
    String endpoint,
    Map<String, dynamic> data, {
    bool includeAuth = true,
  }) async {
    try {
      final url = Uri.parse('${AppConfig.fullApiUrl}$endpoint');
      final response = await http
          .post(
            url,
            headers: _getHeaders(includeAuth: includeAuth),
            body: json.encode(data),
          )
          .timeout(AppConfig.apiTimeout);
      
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection');
    } on HttpException {
      throw ApiException('Server error');
    } on FormatException {
      throw ApiException('Invalid response format');
    }
  }

  /// PUT request
  Future<dynamic> put(
    String endpoint,
    Map<String, dynamic> data, {
    bool includeAuth = true,
  }) async {
    try {
      final url = Uri.parse('${AppConfig.fullApiUrl}$endpoint');
      final response = await http
          .put(
            url,
            headers: _getHeaders(includeAuth: includeAuth),
            body: json.encode(data),
          )
          .timeout(AppConfig.apiTimeout);
      
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection');
    } on HttpException {
      throw ApiException('Server error');
    } on FormatException {
      throw ApiException('Invalid response format');
    }
  }

  /// DELETE request
  Future<dynamic> delete(String endpoint, {bool includeAuth = true}) async {
    try {
      final url = Uri.parse('${AppConfig.fullApiUrl}$endpoint');
      final response = await http
          .delete(url, headers: _getHeaders(includeAuth: includeAuth))
          .timeout(AppConfig.apiTimeout);
      
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection');
    } on HttpException {
      throw ApiException('Server error');
    } on FormatException {
      throw ApiException('Invalid response format');
    }
  }

  /// PATCH request
  Future<dynamic> patch(
    String endpoint,
    Map<String, dynamic> data, {
    bool includeAuth = true,
  }) async {
    try {
      final url = Uri.parse('${AppConfig.fullApiUrl}$endpoint');
      final response = await http
          .patch(
            url,
            headers: _getHeaders(includeAuth: includeAuth),
            body: json.encode(data),
          )
          .timeout(AppConfig.apiTimeout);
      
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection');
    } on HttpException {
      throw ApiException('Server error');
    } on FormatException {
      throw ApiException('Invalid response format');
    }
  }

  /// Refresh the JWT token
  Future<bool> refreshAccessToken() async {
    if (_refreshToken == null) {
      return false;
    }

    try {
      final response = await post(
        '/auth/refresh',
        {'refresh_token': _refreshToken},
        includeAuth: false,
      );

      if (response != null && response['access_token'] != null) {
        await setToken(
          response['access_token'] as String,
          refreshToken: response['refresh_token'] as String?,
        );
        return true;
      }
      return false;
    } catch (e) {
      await clearToken();
      return false;
    }
  }
}

/// Custom exception for API errors
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}
