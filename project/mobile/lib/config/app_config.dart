/// Application configuration
class AppConfig {
  // API Configuration
  static const String apiBaseUrl = 'http://10.41.25.109:8000';
  static const String apiVersion = 'v1';
  static const String apiPrefix = '/api/$apiVersion';

  // WebSocket Configuration
  static const String wsBaseUrl = 'ws://10.41.25.109:8000';
  static const String wsPath = '/api/v1/ws';
  
  // Token Configuration
  static const String tokenKey = 'jwt_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userKey = 'user_data';
  
  // Timeout Configuration
  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration wsReconnectDelay = Duration(seconds: 5);
  
  // Get full API URL
  static String get fullApiUrl => '$apiBaseUrl$apiPrefix';
  
  // Get full WebSocket URL
  static String get fullWsUrl => '$wsBaseUrl$wsPath';
}

// class AppConfig {
//   static const String apiBaseUrl = 'http://localhost:8000';
//   static const String apiVersion = 'v1';
// }