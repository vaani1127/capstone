/// Doctor model representing a healthcare provider
class Doctor {
  final int id;
  final int userId;
  final String name;
  final String specialization;
  final String? licenseNumber;
  final int averageConsultationDuration;

  Doctor({
    required this.id,
    required this.userId,
    required this.name,
    required this.specialization,
    this.licenseNumber,
    required this.averageConsultationDuration,
  });

  factory Doctor.fromJson(Map<String, dynamic> json) {
    return Doctor(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      name: json['name'] as String,
      specialization: json['specialization'] as String? ?? 'General Medicine',
      licenseNumber: json['license_number'] as String?,
      averageConsultationDuration: json['average_consultation_duration'] as int? ?? 15,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'name': name,
      'specialization': specialization,
      'license_number': licenseNumber,
      'average_consultation_duration': averageConsultationDuration,
    };
  }
}
