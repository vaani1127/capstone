import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;
import '../config/app_config.dart';
import 'api_client.dart';

/// WebSocket service for real-time communication
class WebSocketService {
  static final WebSocketService _instance = WebSocketService._internal();
  factory WebSocketService() => _instance;
  WebSocketService._internal();

  WebSocketChannel? _channel;
  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  final _connectionController = StreamController<bool>.broadcast();
  Timer? _reconnectTimer;
  bool _isConnecting = false;
  bool _shouldReconnect = true;

  /// Stream of incoming messages
  Stream<Map<String, dynamic>> get messages => _messageController.stream;

  /// Stream of connection status
  Stream<bool> get connectionStatus => _connectionController.stream;

  /// Check if WebSocket is connected
  bool get isConnected => _channel != null;

  /// Connect to WebSocket server with JWT authentication
  /// Failures are handled silently and reconnection is scheduled automatically
  Future<void> connect() async {
    if (_isConnecting || isConnected) {
      return;
    }

    _isConnecting = true;
    _shouldReconnect = true;

    try {
      final apiClient = ApiClient();
      final token = apiClient.token;

      if (token == null) {
        _isConnecting = false;
        return; // No token available, don't throw - just return silently
      }

      // Build WebSocket URL with token as query parameter
      final wsUrl = '${AppConfig.fullWsUrl}?token=$token';
      final uri = Uri.parse(wsUrl);

      _channel = WebSocketChannel.connect(uri);

      // Listen to messages
      _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
        cancelOnError: false,
      );

      _connectionController.add(true);
      _isConnecting = false;
    } catch (e) {
      // Silently handle connection errors - don't crash the app
      _isConnecting = false;
      _connectionController.add(false);
      _scheduleReconnect();
    }
  }

  /// Handle incoming messages
  void _onMessage(dynamic message) {
    try {
      final data = json.decode(message as String) as Map<String, dynamic>;
      _messageController.add(data);
    } catch (e) {
      // Invalid message format
    }
  }

  /// Handle WebSocket errors
  void _onError(dynamic error) {
    _connectionController.add(false);
    _scheduleReconnect();
  }

  /// Handle WebSocket connection closed
  void _onDone() {
    _channel = null;
    _connectionController.add(false);
    _scheduleReconnect();
  }

  /// Schedule reconnection attempt
  void _scheduleReconnect() {
    if (!_shouldReconnect) {
      return;
    }

    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(AppConfig.wsReconnectDelay, () {
      if (_shouldReconnect && !isConnected) {
        connect();
      }
    });
  }

  /// Send a message through WebSocket
  void send(Map<String, dynamic> message) {
    if (_channel != null) {
      _channel!.sink.add(json.encode(message));
    }
  }

  /// Subscribe to a specific event type
  Stream<Map<String, dynamic>> on(String eventType) {
    return messages.where((message) => message['event'] == eventType);
  }

  /// Subscribe to queue updates
  Stream<Map<String, dynamic>> get queueUpdates => on('queue_update');

  /// Subscribe to appointment status updates
  Stream<Map<String, dynamic>> get appointmentUpdates => on('appointment_status');

  /// Disconnect from WebSocket server
  Future<void> disconnect() async {
    _shouldReconnect = false;
    _reconnectTimer?.cancel();
    
    if (_channel != null) {
      await _channel!.sink.close(status.goingAway);
      _channel = null;
    }
    
    _connectionController.add(false);
  }

  /// Dispose resources
  void dispose() {
    disconnect();
    _messageController.close();
    _connectionController.close();
  }
}
