import 'api_integration_test.dart' as api_tests;
import 'websocket_integration_test.dart' as websocket_tests;
import 'navigation_flow_test.dart' as navigation_tests;

/// Main entry point for all integration tests
/// 
/// This file imports and runs all integration test suites.
/// Run with: flutter test integration_test/all_tests.dart
void main() {
  api_tests.main();
  websocket_tests.main();
  navigation_tests.main();
}
