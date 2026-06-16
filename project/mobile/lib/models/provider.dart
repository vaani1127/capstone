/// Provider model representing a healthcare provider.
class Provider {
  final int id;
  final int? userId;
  final int? organizationId;
  final String? organizationName;
  final String name;
  final String? gender;
  final String? speciality;
  final String? address;
  final String? city;
  final String? state;
  final String? zip;
  final double? lat;
  final double? lon;
  final int encounterCount;
  final int procedureCount;
  final DateTime createdAt;

  Provider({
    required this.id,
    this.userId,
    this.organizationId,
    this.organizationName,
    required this.name,
    this.gender,
    this.speciality,
    this.address,
    this.city,
    this.state,
    this.zip,
    this.lat,
    this.lon,
    required this.encounterCount,
    required this.procedureCount,
    required this.createdAt,
  });

  factory Provider.fromJson(Map<String, dynamic> json) {
    return Provider(
      id: json['id'] as int,
      userId: json['user_id'] as int?,
      organizationId: json['organization_id'] as int?,
      organizationName: json['organization_name'] as String?,
      name: json['name'] as String,
      gender: json['gender'] as String?,
      speciality: json['speciality'] as String?,
      address: json['address'] as String?,
      city: json['city'] as String?,
      state: json['state'] as String?,
      zip: json['zip'] as String?,
      lat: (json['lat'] as num?)?.toDouble(),
      lon: (json['lon'] as num?)?.toDouble(),
      encounterCount: json['encounter_count'] as int? ?? 0,
      procedureCount: json['procedure_count'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  /// Formatted city/state string for list display.
  String get location {
    if (city != null && state != null) return '$city, $state';
    if (city != null) return city!;
    if (state != null) return state!;
    return 'Unknown';
  }
}
