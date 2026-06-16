import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';
import '../config/app_config.dart';
import 'api_client.dart';

/// Authentication service for user login and registration
class AuthService {
  final ApiClient _apiClient = ApiClient();

  /// Register a new user.
  ///
  /// The backend returns the new UserResponse directly (no token on register).
  /// The caller should call [login] afterwards to obtain tokens.
  Future<User> register({
    required String name,
    required String email,
    required String password,
    required String role,
  }) async {
    final response = await _apiClient.post(
      '/auth/register',
      {
        'name': name,
        'email': email,
        'password': password,
        'role': role,
      },
      includeAuth: false,
    );

    // Backend returns UserResponse directly (not wrapped)
    final user = User.fromJson(response as Map<String, dynamic>);
    await _saveUser(user);
    return user;
  }

  /// Login with email and password
  Future<User> login({
    required String email,
    required String password,
  }) async {
    final response = await _apiClient.post(
      '/auth/login',
      {
        'email': email,
        'password': password,
      },
      includeAuth: false,
    );

    final user = User.fromJson(response['user']);
    final token = response['access_token'] as String;
    final refreshToken = response['refresh_token'] as String?;
    
    await _apiClient.setToken(token, refreshToken: refreshToken);
    await _saveUser(user);
    
    return user;
  }

  /// Logout the current user
  Future<void> logout() async {
    await _apiClient.clearToken();
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConfig.userKey);
  }

  /// Get the current logged-in user
  Future<User?> getCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString(AppConfig.userKey);
    
    if (userJson == null) {
      return null;
    }
    
    return User.fromJson(json.decode(userJson));
  }

  /// Save user data to local storage
  Future<void> _saveUser(User user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConfig.userKey, json.encode(user.toJson()));
  }

  /// Check if user is authenticated
  bool get isAuthenticated => _apiClient.isAuthenticated;
}
