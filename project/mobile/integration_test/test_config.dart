/// Test configuration for integration tests
/// 
/// This file contains configuration and helper functions for integration tests.
class TestConfig {
  // Test user credentials
  static const String patientEmail = 'patient@test.com';
  static const String patientPassword = 'password123';
  
  static const String doctorEmail = 'doctor@test.com';
  static const String doctorPassword = 'password123';
  
  static const String nurseEmail = 'nurse@test.com';
  static const String nursePassword = 'password123';
  
  static const String adminEmail = 'admin@test.com';
  static const String adminPassword = 'password123';
  
  // Test timeouts
  static const Duration shortTimeout = Duration(seconds: 2);
  static const Duration mediumTimeout = Duration(seconds: 5);
  static const Duration longTimeout = Duration(seconds: 10);
  
  // Backend requirements
  static const bool requiresBackend = true;
  static const String backendUrl = 'http://localhost:8000';
  static const String wsUrl = 'ws://localhost:8000/ws';
  
  // Test data
  static const String testPatientName = 'Test Patient';
  static const String testPatientEmail = 'testpatient@test.com';
  static const String testPatientPhone = '1234567890';
}
