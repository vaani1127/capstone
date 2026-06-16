/// Appointment model representing a scheduled or walk-in appointment
class Appointment {
  final int id;
  final int patientId;
  final int doctorId;
  final DateTime scheduledTime;
  final String status;
  final String appointmentType;
  final int? queuePosition;
  final String? doctorName;
  final String? patientName;
  final DateTime createdAt;

  Appointment({
    required this.id,
    required this.patientId,
    required this.doctorId,
    required this.scheduledTime,
    required this.status,
    required this.appointmentType,
    this.queuePosition,
    this.doctorName,
    this.patientName,
    required this.createdAt,
  });

  factory Appointment.fromJson(Map<String, dynamic> json) {
    return Appointment(
      id: json['id'] as int,
      patientId: json['patient_id'] as int,
      doctorId: json['doctor_id'] as int,
      scheduledTime: DateTime.parse(json['scheduled_time'] as String),
      status: json['status'] as String,
      appointmentType: json['appointment_type'] as String,
      queuePosition: json['queue_position'] as int?,
      doctorName: json['doctor_name'] as String?,
      patientName: json['patient_name'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'patient_id': patientId,
      'doctor_id': doctorId,
      'scheduled_time': scheduledTime.toIso8601String(),
      'status': status,
      'appointment_type': appointmentType,
      'queue_position': queuePosition,
      'doctor_name': doctorName,
      'patient_name': patientName,
      'created_at': createdAt.toIso8601String(),
    };
  }

  bool get isScheduled => status == 'scheduled';
  bool get isCheckedIn => status == 'checked_in';
  bool get isInProgress => status == 'in_progress';
  bool get isCompleted => status == 'completed';
  bool get isCancelled => status == 'cancelled';
  bool get isWalkIn => appointmentType == 'walk_in';
}
