/// Medical record model representing consultation notes and prescriptions
class MedicalRecord {
  final int id;
  final int patientId;
  final int doctorId;
  final int? appointmentId;
  final String? consultationNotes;
  final String? diagnosis;
  final String? prescription;
  final int versionNumber;
  final int? parentRecordId;
  final int createdBy;
  final String? doctorName;
  final DateTime createdAt;
  final bool? isTampered;

  MedicalRecord({
    required this.id,
    required this.patientId,
    required this.doctorId,
    this.appointmentId,
    this.consultationNotes,
    this.diagnosis,
    this.prescription,
    required this.versionNumber,
    this.parentRecordId,
    required this.createdBy,
    this.doctorName,
    required this.createdAt,
    this.isTampered,
  });

  factory MedicalRecord.fromJson(Map<String, dynamic> json) {
    return MedicalRecord(
      id: json['id'] as int,
      patientId: json['patient_id'] as int,
      doctorId: json['doctor_id'] as int,
      appointmentId: json['appointment_id'] as int?,
      consultationNotes: json['consultation_notes'] as String?,
      diagnosis: json['diagnosis'] as String?,
      prescription: json['prescription'] as String?,
      versionNumber: json['version_number'] as int? ?? 1,
      parentRecordId: json['parent_record_id'] as int?,
      createdBy: json['created_by'] as int,
      doctorName: json['doctor_name'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      isTampered: json['is_tampered'] as bool?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'patient_id': patientId,
      'doctor_id': doctorId,
      'appointment_id': appointmentId,
      'consultation_notes': consultationNotes,
      'diagnosis': diagnosis,
      'prescription': prescription,
      'version_number': versionNumber,
      'parent_record_id': parentRecordId,
      'created_by': createdBy,
      'doctor_name': doctorName,
      'created_at': createdAt.toIso8601String(),
      'is_tampered': isTampered,
    };
  }

  bool get hasConsultationNotes => consultationNotes != null && consultationNotes!.isNotEmpty;
  bool get hasPrescription => prescription != null && prescription!.isNotEmpty;
  bool get isOriginal => versionNumber == 1;
}
