/// Vitals model representing a single set of vital sign measurements
class Vitals {
  final int id;
  final int patientId;
  final int? appointmentId;
  final int recordedBy;
  final String? recordedByName;
  final DateTime recordedAt;
  final int? systolicBp;
  final int? diastolicBp;
  final int? heartRate;
  final double? temperature;
  final int? respiratoryRate;
  final double? oxygenSaturation;
  final double? weightKg;
  final double? heightCm;
  final double? bmi;
  final String? notes;
  final DateTime createdAt;

  Vitals({
    required this.id,
    required this.patientId,
    this.appointmentId,
    required this.recordedBy,
    this.recordedByName,
    required this.recordedAt,
    this.systolicBp,
    this.diastolicBp,
    this.heartRate,
    this.temperature,
    this.respiratoryRate,
    this.oxygenSaturation,
    this.weightKg,
    this.heightCm,
    this.bmi,
    this.notes,
    required this.createdAt,
  });

  factory Vitals.fromJson(Map<String, dynamic> json) {
    return Vitals(
      id: json['id'] as int,
      patientId: json['patient_id'] as int,
      appointmentId: json['appointment_id'] as int?,
      recordedBy: json['recorded_by'] as int,
      recordedByName: json['recorded_by_name'] as String?,
      recordedAt: DateTime.parse(json['recorded_at'] as String),
      systolicBp: json['systolic_bp'] as int?,
      diastolicBp: json['diastolic_bp'] as int?,
      heartRate: json['heart_rate'] as int?,
      temperature: (json['temperature'] as num?)?.toDouble(),
      respiratoryRate: json['respiratory_rate'] as int?,
      oxygenSaturation: (json['oxygen_saturation'] as num?)?.toDouble(),
      weightKg: (json['weight_kg'] as num?)?.toDouble(),
      heightCm: (json['height_cm'] as num?)?.toDouble(),
      bmi: (json['bmi'] as num?)?.toDouble(),
      notes: json['notes'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'patient_id': patientId,
      'appointment_id': appointmentId,
      'recorded_by': recordedBy,
      'recorded_by_name': recordedByName,
      'recorded_at': recordedAt.toIso8601String(),
      'systolic_bp': systolicBp,
      'diastolic_bp': diastolicBp,
      'heart_rate': heartRate,
      'temperature': temperature,
      'respiratory_rate': respiratoryRate,
      'oxygen_saturation': oxygenSaturation,
      'weight_kg': weightKg,
      'height_cm': heightCm,
      'bmi': bmi,
      'notes': notes,
      'created_at': createdAt.toIso8601String(),
    };
  }

  /// True if systolic > 140 or diastolic > 90 (hypertension threshold)
  bool get isBpElevated =>
      (systolicBp != null && systolicBp! > 140) ||
      (diastolicBp != null && diastolicBp! > 90);

  /// True if heart rate > 100 bpm (tachycardia) or < 50 bpm (bradycardia)
  bool get isHeartRateAbnormal =>
      heartRate != null && (heartRate! > 100 || heartRate! < 50);

  /// True if SpO2 < 95%
  bool get isSpO2Low => oxygenSaturation != null && oxygenSaturation! < 95;

  /// True if temperature > 99.5°F (low-grade fever threshold)
  bool get isTempElevated => temperature != null && temperature! > 99.5;
}
