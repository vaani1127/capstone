/// Patient model representing a patient in the system
class Patient {
  final int id;
  final int userId;
  final String name;
  final String? email;
  final String? phone;
  final DateTime? dateOfBirth;
  final String? gender;
  final String? address;
  final String? bloodGroup;

  Patient({
    required this.id,
    required this.userId,
    required this.name,
    this.email,
    this.phone,
    this.dateOfBirth,
    this.gender,
    this.address,
    this.bloodGroup,
  });

  factory Patient.fromJson(Map<String, dynamic> json) {
    return Patient(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      name: json['name'] as String,
      email: json['email'] as String?,
      phone: json['phone'] as String?,
      dateOfBirth: json['date_of_birth'] != null
          ? DateTime.parse(json['date_of_birth'] as String)
          : null,
      gender: json['gender'] as String?,
      address: json['address'] as String?,
      bloodGroup: json['blood_group'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'name': name,
      'email': email,
      'phone': phone,
      'date_of_birth': dateOfBirth?.toIso8601String(),
      'gender': gender,
      'address': address,
      'blood_group': bloodGroup,
    };
  }
}
