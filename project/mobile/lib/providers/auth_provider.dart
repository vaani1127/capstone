import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import '../models/user.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/websocket_service.dart';

/// Provider for authentication state management
class AuthProvider with ChangeNotifier {
  final AuthService _authService = AuthService();
  final WebSocketService _wsService = WebSocketService();
  
  User? _currentUser;
  bool _isLoading = false;
  String? _error;

  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _currentUser != null;

  /// Initialize auth provider
  Future<void> initialize() async {
    _isLoading = true;
    // Don't notify during init - just fetch the data
    try {
      // Restore token from SharedPreferences into memory BEFORE any API call.
      await ApiClient().initialize();
      _currentUser = await _authService.getCurrentUser();
      // Only treat as authenticated if BOTH user data and token are present.
      if (_currentUser != null && !ApiClient().isAuthenticated) {
        _currentUser = null; // token expired or missing — force re-login
      }
      if (_currentUser != null) {
        await _wsService.connect();
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      // Only notify after initialization is complete
      WidgetsBinding.instance.addPostFrameCallback((_) {
        notifyListeners();
      });
    }
  }

  /// Login with email and password
  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _currentUser = await _authService.login(email: email, password: password);
      await _wsService.connect();
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// Register a new user
  Future<bool> register({
    required String name,
    required String email,
    required String password,
    required String role,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _currentUser = await _authService.register(
        name: name,
        email: email,
        password: password,
        role: role,
      );
      await _wsService.connect();
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// Logout the current user
  Future<void> logout() async {
    await _authService.logout();
    await _wsService.disconnect();
    _currentUser = null;
    notifyListeners();
  }

  /// Clear error message
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
